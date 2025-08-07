"""Code generation utilities for database models and DAOs."""
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

from .logger import success
@dataclass
class DatabaseColumn:
    """Represents a database column."""

    name: str
    column_type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    
    @property
    def rust_type(self) -> str:
        """Convert database type to Rust type."""
        type_mapping = {
            'TEXT': 'String',
            'VARCHAR': 'String',
            'INTEGER': 'i32',
            'BIGINT': 'i64',
            'BOOLEAN': 'bool',
            'TIMESTAMP': 'DateTime<Utc>',
            'UUID': 'Uuid',
            'JSONB': 'serde_json::Value',
        }
        
        rust_type = type_mapping.get(self.column_type.upper(), 'String')
        
        if self.nullable and not self.primary_key:
            return f'Option<{rust_type}>'
        
        return rust_type
    
    @property
    def cpp_type(self) -> str:
        """Convert database type to C++ type."""
        type_mapping = {
            'TEXT': 'std::string',
            'VARCHAR': 'std::string',
            'INTEGER': 'int',
            'BIGINT': 'int64_t',
            'BOOLEAN': 'bool',
            'TIMESTAMP': 'std::chrono::system_clock::time_point',
            'UUID': 'std::string',
            'JSONB': 'nlohmann::json',
        }
        
        cpp_type = type_mapping.get(self.column_type.upper(), 'std::string')
        
        if self.nullable and not self.primary_key:
            return f'std::optional<{cpp_type}>'
        
        return cpp_type
    
    @property
    def python_type(self) -> str:
        """Convert database type to Python type."""
        type_mapping = {
            'TEXT': 'str',
            'VARCHAR': 'str',
            'INTEGER': 'int',
            'BIGINT': 'int',
            'BOOLEAN': 'bool',
            'TIMESTAMP': 'datetime',
            'UUID': 'UUID',
            'JSONB': 'dict',
        }
        
        py_type = type_mapping.get(self.column_type.upper(), 'str')
        
        if self.nullable and not self.primary_key:
            return f'Optional[{py_type}]'
        
        return py_type
    
    @property
    def go_type(self) -> str:
        """Convert database type to Go type."""
        type_mapping = {
            'TEXT': 'string',
            'VARCHAR': 'string',
            'INTEGER': 'int',
            'BIGINT': 'int64',
            'BOOLEAN': 'bool',
            'TIMESTAMP': 'time.Time',
            'UUID': 'uuid.UUID',
            'JSONB': 'map[string]interface{}',
        }
        
        go_type = type_mapping.get(self.column_type.upper(), 'string')
        
        if self.nullable and not self.primary_key:
            return f'*{go_type}'
        
        return go_type


@dataclass
class DatabaseTable:
    """Represents a database table."""

    name: str
    columns: List[DatabaseColumn] = field(default_factory=list)
    
    @property
    def struct_name(self) -> str:
        """Convert table name to Rust struct name."""
        return ''.join(word.capitalize() for word in self.name.split('_'))
    
    @property
    def primary_key(self) -> Optional[DatabaseColumn]:
        """Get the primary key column."""
        for col in self.columns:
            if col.primary_key:
                return col
        return None


class RustDAOGenerator:
    """Generates Rust DAO code from database schema."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def parse_sql_schema(self, schema_content: str) -> List[DatabaseTable]:
        """Parse SQL schema and extract table definitions."""
        tables = []
        
        # Simple regex to extract CREATE TABLE statements
        table_pattern = r'CREATE TABLE\s+(\w+)\s*\((.*?)\);'
        
        for match in re.finditer(table_pattern, schema_content, re.DOTALL | re.IGNORECASE):
            table_name = match.group(1)
            columns_str = match.group(2)
            
            columns = self._parse_columns(columns_str)
            tables.append(DatabaseTable(table_name, columns))
        
        return tables
    
    def _parse_columns(self, columns_str: str) -> List[DatabaseColumn]:
        """Parse column definitions from CREATE TABLE statement."""
        columns = []
        
        # Split by comma, but be careful with constraints
        lines = [line.strip() for line in columns_str.split('\n') if line.strip()]
        
        for line in lines:
            if line.startswith('CONSTRAINT') or line.startswith('PRIMARY KEY') or line.startswith('FOREIGN KEY'):
                continue
                
            # Simple column parsing
            parts = line.replace(',', '').split()
            if len(parts) >= 2:
                name = parts[0]
                col_type = parts[1]
                
                nullable = 'NOT NULL' not in line.upper()
                primary_key = 'PRIMARY KEY' in line.upper()
                
                columns.append(DatabaseColumn(name, col_type, nullable, primary_key))
        
        return columns
    
    def generate_model(self, table: DatabaseTable) -> str:
        """Generate Rust model struct."""
        imports = [
            "use chrono::{DateTime, Utc};",
            "use serde::{Deserialize, Serialize};",
            "use utoipa::ToSchema;",
            "use uuid::Uuid;",
        ]
        
        fields = []
        for col in table.columns:
            doc_comment = f"    /// {col.name.replace('_', ' ').title()}"
            field_name = col.name
            field_type = col.rust_type
            
            fields.append(f"{doc_comment}\n    pub {field_name}: {field_type},")
        
        return f'''
{chr(10).join(imports)}

/// Represents a {table.name} in the system
#[derive(Debug, Clone, Serialize, Deserialize, ToSchema)]
pub struct {table.struct_name} {{
{chr(10).join(fields)}
}}
'''.strip()
    
    def generate_dao_trait(self, table: DatabaseTable) -> str:
        """Generate DAO trait for the table."""
        struct_name = table.struct_name
        trait_name = f"{struct_name}DAO"
        pk = table.primary_key
        pk_type = pk.rust_type if pk else 'Uuid'
        
        methods = [
            f"    /// Find {table.name} by ID",
            f"    async fn find_by_id(&self, id: {pk_type}) -> Result<Option<{struct_name}>, DatabaseError>;",
            "",
            f"    /// Find all {table.name}",
            f"    async fn find_all(&self) -> Result<Vec<{struct_name}>, DatabaseError>;",
            "",
            f"    /// Create a new {table.name}",
            f"    async fn create(&self, entity: &{struct_name}) -> Result<{pk_type}, DatabaseError>;",
            "",
            f"    /// Update {table.name}",
            f"    async fn update(&self, id: {pk_type}, entity: &{struct_name}) -> Result<(), DatabaseError>;",
            "",
            f"    /// Delete {table.name}",
            f"    async fn delete(&self, id: {pk_type}) -> Result<(), DatabaseError>;",
        ]
        
        return f'''
use crate::model::error::DatabaseError;
use crate::model::{struct_name.lower()}::model::{struct_name};
use async_trait::async_trait;
use uuid::Uuid;
use std::sync::Arc;

#[async_trait]
pub trait {trait_name}: Send + Sync {{
{chr(10).join(methods)}
}}
'''.strip()
    
    def generate_pg_dao_impl(self, table: DatabaseTable) -> str:
        """Generate PostgreSQL DAO implementation."""
        struct_name = table.struct_name
        trait_name = f"{struct_name}DAO"
        impl_name = f"Pg{struct_name}DAO"
        pk = table.primary_key
        pk_type = pk.rust_type if pk else 'Uuid'
        
        return f'''
use super::dao::{trait_name};
use crate::model::error::DatabaseError;
use crate::model::{struct_name.lower()}::model::{struct_name};
use async_trait::async_trait;
use sqlx::{{PgPool, Row}};
use std::sync::Arc;
use uuid::Uuid;

pub struct {impl_name} {{
    pool: Arc<PgPool>,
}}

impl {impl_name} {{
    pub fn new(pool: Arc<PgPool>) -> Self {{
        Self {{ pool }}
    }}
}}

#[async_trait]
impl {trait_name} for {impl_name} {{
    async fn find_by_id(&self, id: {pk_type}) -> Result<Option<{struct_name}>, DatabaseError> {{
        let query = "SELECT * FROM {table.name} WHERE {pk.name if pk else 'id'} = $1";
        
        match sqlx::query(query)
            .bind(id)
            .fetch_optional(self.pool.as_ref())
            .await
        {{
            Ok(Some(row)) => {{
                let entity = {struct_name} {{
{self._generate_field_mapping(table, "                    ")}
                }};
                Ok(Some(entity))
            }},
            Ok(None) => Ok(None),
            Err(e) => Err(DatabaseError::QueryError(e.to_string())),
        }}
    }}
    
    async fn find_all(&self) -> Result<Vec<{struct_name}>, DatabaseError> {{
        let query = "SELECT * FROM {table.name}";
        
        match sqlx::query(query)
            .fetch_all(self.pool.as_ref())
            .await
        {{
            Ok(rows) => {{
                let entities: Vec<{struct_name}> = rows
                    .into_iter()
                    .map(|row| {struct_name} {{
{self._generate_field_mapping(table, "                        ")}
                    }})
                    .collect();
                Ok(entities)
            }},
            Err(e) => Err(DatabaseError::QueryError(e.to_string())),
        }}
    }}
    
    async fn create(&self, entity: &{struct_name}) -> Result<{pk_type}, DatabaseError> {{
        // Implementation would go here
        todo!("Implement create method")
    }}
    
    async fn update(&self, id: {pk_type}, entity: &{struct_name}) -> Result<(), DatabaseError> {{
        // Implementation would go here
        todo!("Implement update method")
    }}
    
    async fn delete(&self, id: {pk_type}) -> Result<(), DatabaseError> {{
        let query = "DELETE FROM {table.name} WHERE {pk.name if pk else 'id'} = $1";
        
        match sqlx::query(query)
            .bind(id)
            .execute(self.pool.as_ref())
            .await
        {{
            Ok(_) => Ok(()),
            Err(e) => Err(DatabaseError::QueryError(e.to_string())),
        }}
    }}
}}
'''.strip()
    
    def _generate_field_mapping(self, table: DatabaseTable, indent: str) -> str:
        """Generate field mapping from SQL row to struct."""
        mappings = []
        for col in table.columns:
            if col.rust_type.startswith('Option<'):
                inner_type = col.rust_type[7:-1]  # Remove Option< and >
                mappings.append(f'{indent}{col.name}: row.try_get("{col.name}").ok(),')
            else:
                mappings.append(f'{indent}{col.name}: row.get("{col.name}"),')
        
        return '\n'.join(mappings)
    
    def generate_mock_dao(self, table: DatabaseTable) -> str:
        """Generate mock DAO for testing."""
        struct_name = table.struct_name
        trait_name = f"{struct_name}DAO"
        mock_name = f"Mock{struct_name}DAO"
        pk_type = table.primary_key.rust_type if table.primary_key else 'Uuid'
        
        return f'''
use super::dao::{trait_name};
use crate::model::error::DatabaseError;
use crate::model::{struct_name.lower()}::model::{struct_name};
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::{{Arc, Mutex}};
use uuid::Uuid;

#[derive(Debug, Clone, Default)]
pub struct {mock_name} {{
    entities: Arc<Mutex<HashMap<{pk_type}, {struct_name}>>>,
}}

impl {mock_name} {{
    pub fn new() -> Self {{
        Self::default()
    }}
    
    pub fn with_data(entities: Vec<{struct_name}>) -> Self {{
        let mut map = HashMap::new();
        for entity in entities {{
            map.insert(entity.{table.primary_key.name if table.primary_key else 'id'}, entity);
        }}
        
        Self {{
            entities: Arc::new(Mutex::new(map)),
        }}
    }}
}}

#[async_trait]
impl {trait_name} for {mock_name} {{
    async fn find_by_id(&self, id: {pk_type}) -> Result<Option<{struct_name}>, DatabaseError> {{
        let entities = self.entities.lock().unwrap();
        Ok(entities.get(&id).cloned())
    }}
    
    async fn find_all(&self) -> Result<Vec<{struct_name}>, DatabaseError> {{
        let entities = self.entities.lock().unwrap();
        Ok(entities.values().cloned().collect())
    }}
    
    async fn create(&self, entity: &{struct_name}) -> Result<{pk_type}, DatabaseError> {{
        let mut entities = self.entities.lock().unwrap();
        let id = entity.{table.primary_key.name if table.primary_key else 'id'};
        entities.insert(id, entity.clone());
        Ok(id)
    }}
    
    async fn update(&self, id: {pk_type}, entity: &{struct_name}) -> Result<(), DatabaseError> {{
        let mut entities = self.entities.lock().unwrap();
        entities.insert(id, entity.clone());
        Ok(())
    }}
    
    async fn delete(&self, id: {pk_type}) -> Result<(), DatabaseError> {{
        let mut entities = self.entities.lock().unwrap();
        entities.remove(&id);
        Ok(())
    }}
}}
'''.strip()


def generate_rust_dao_from_schema(schema_file: str, output_dir: str, service_name: str):
    """Generate complete DAO structure from SQL schema."""
    generator = RustDAOGenerator(service_name)
    
    # Read schema file
    with open(schema_file, 'r') as f:
        schema_content = f.read()
    
    # Parse tables
    tables = generator.parse_sql_schema(schema_content)
    
    output_path = Path(output_dir)
    
    for table in tables:
        table_dir = output_path / f"model/{table.name}"
        table_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate model
        with open(table_dir / "model.rs", 'w') as f:
            f.write(generator.generate_model(table))
        
        # Generate DAO trait
        with open(table_dir / "dao.rs", 'w') as f:
            f.write(generator.generate_dao_trait(table))
        
        # Generate PostgreSQL implementation
        with open(table_dir / "pg_dao.rs", 'w') as f:
            f.write(generator.generate_pg_dao_impl(table))
        
        # Generate mock DAO
        with open(table_dir / "mock_dao.rs", 'w') as f:
            f.write(generator.generate_mock_dao(table))
        
        # Generate mod.rs
        with open(table_dir / "mod.rs", 'w') as f:
            f.write(f'''pub mod dao;
pub mod model;
pub mod pg_dao;
pub mod mock_dao;
pub mod error;
pub mod response;

pub use dao::*;
pub use model::*;
pub use pg_dao::*;
pub use mock_dao::*;
''')
    
    success(f"Generated DAO structure for {len(tables)} tables in {output_dir}")


class CppDAOGenerator:
    """Generates C++ DAO code from database schema."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def generate_model(self, table: DatabaseTable) -> str:
        """Generate C++ model struct."""
        includes = [
            "#pragma once",
            "#include <string>",
            "#include <optional>",
            "#include <chrono>",
            "#include <nlohmann/json.hpp>",
        ]
        
        fields = []
        for col in table.columns:
            field_type = col.cpp_type
            field_name = col.name
            fields.append(f"    {field_type} {field_name};")
        
        return f'''
{chr(10).join(includes)}

namespace models {{

/// Represents a {table.name} in the system
struct {table.struct_name} {{
{chr(10).join(fields)}
    
    // Convert to JSON
    nlohmann::json to_json() const;
    
    // Create from JSON
    static {table.struct_name} from_json(const nlohmann::json& j);
    
    // Equality operator
    bool operator==(const {table.struct_name}& other) const;
}};

// JSON serialization functions
void to_json(nlohmann::json& j, const {table.struct_name}& obj);
void from_json(const nlohmann::json& j, {table.struct_name}& obj);

}} // namespace models
'''.strip()
    
    def generate_dao_interface(self, table: DatabaseTable) -> str:
        """Generate DAO interface for C++."""
        struct_name = table.struct_name
        interface_name = f"{struct_name}DAO"
        pk = table.primary_key
        pk_type = pk.cpp_type if pk else 'std::string'
        
        return f'''
#pragma once
#include "models/{table.name}.hpp"
#include <vector>
#include <optional>
#include <memory>
#include <future>

namespace dao {{

class {interface_name} {{
public:
    virtual ~{interface_name}() = default;
    
    /// Find {table.name} by ID
    virtual std::future<std::optional<models::{struct_name}>> find_by_id(const {pk_type}& id) = 0;
    
    /// Find all {table.name}
    virtual std::future<std::vector<models::{struct_name}>> find_all() = 0;
    
    /// Create a new {table.name}
    virtual std::future<{pk_type}> create(const models::{struct_name}& entity) = 0;
    
    /// Update {table.name}
    virtual std::future<bool> update(const {pk_type}& id, const models::{struct_name}& entity) = 0;
    
    /// Delete {table.name}
    virtual std::future<bool> delete_entity(const {pk_type}& id) = 0;
}};

}} // namespace dao
'''.strip()
    
    def generate_pg_dao_impl(self, table: DatabaseTable) -> str:
        """Generate PostgreSQL DAO implementation for C++."""
        struct_name = table.struct_name
        interface_name = f"{struct_name}DAO"
        impl_name = f"Pg{struct_name}DAO"
        pk = table.primary_key
        pk_type = pk.cpp_type if pk else 'std::string'
        
        return f'''
#pragma once
#include "dao/{table.name}_dao.hpp"
#include <pqxx/pqxx>
#include <memory>

namespace dao {{

class {impl_name} : public {interface_name} {{
private:
    std::shared_ptr<pqxx::connection> connection_;
    
public:
    explicit {impl_name}(std::shared_ptr<pqxx::connection> conn);
    
    std::future<std::optional<models::{struct_name}>> find_by_id(const {pk_type}& id) override;
    std::future<std::vector<models::{struct_name}>> find_all() override;
    std::future<{pk_type}> create(const models::{struct_name}& entity) override;
    std::future<bool> update(const {pk_type}& id, const models::{struct_name}& entity) override;
    std::future<bool> delete_entity(const {pk_type}& id) override;
    
private:
    models::{struct_name} row_to_entity(const pqxx::row& row);
}};

}} // namespace dao
'''.strip()


class PythonDAOGenerator:
    """Generates Python DAO code from database schema."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def generate_model(self, table: DatabaseTable) -> str:
        """Generate Python model using Pydantic."""
        imports = [
            "from datetime import datetime",
            "from typing import Optional",
            "from uuid import UUID",
            "from pydantic import BaseModel, Field",
        ]
        
        fields = []
        for col in table.columns:
            field_type = col.python_type
            field_name = col.name
            
            if col.primary_key:
                fields.append(f"    {field_name}: {field_type} = Field(..., description='{col.name.replace('_', ' ').title()}')")
            else:
                default = "None" if col.nullable else "..."
                fields.append(f"    {field_name}: {field_type} = Field({default}, description='{col.name.replace('_', ' ').title()}')")
        
        return f'''
{chr(10).join(imports)}


class {table.struct_name}(BaseModel):
    """Represents a {table.name} in the system."""
    
{chr(10).join(fields)}
    
    class Config:
        from_attributes = True
        json_encoders = {{
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }}


class {table.struct_name}Create(BaseModel):
    """Schema for creating a {table.name}."""
    
{chr(10).join([f"    {col.name}: {col.python_type}" for col in table.columns if not col.primary_key])}


class {table.struct_name}Update(BaseModel):
    """Schema for updating a {table.name}."""
    
{chr(10).join([f"    {col.name}: Optional[{col.python_type}] = None" for col in table.columns if not col.primary_key])}
'''.strip()
    
    def generate_dao_interface(self, table: DatabaseTable) -> str:
        """Generate DAO interface for Python."""
        struct_name = table.struct_name
        pk = table.primary_key
        pk_type = pk.python_type if pk else 'UUID'
        
        return f'''
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from .models import {struct_name}, {struct_name}Create, {struct_name}Update


class {struct_name}DAO(ABC):
    """Abstract DAO for {table.name} operations."""
    
    @abstractmethod
    async def find_by_id(self, entity_id: {pk_type}) -> Optional[{struct_name}]:
        """Find {table.name} by ID."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[{struct_name}]:
        """Find all {table.name}."""
        pass
    
    @abstractmethod
    async def create(self, entity: {struct_name}Create) -> {struct_name}:
        """Create a new {table.name}."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: {pk_type}, entity: {struct_name}Update) -> Optional[{struct_name}]:
        """Update {table.name}."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: {pk_type}) -> bool:
        """Delete {table.name}."""
        pass
'''.strip()
    
    def generate_sqlalchemy_dao(self, table: DatabaseTable) -> str:
        """Generate SQLAlchemy DAO implementation."""
        struct_name = table.struct_name
        pk = table.primary_key
        pk_type = pk.python_type if pk else 'UUID'
        
        return f'''
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .dao import {struct_name}DAO
from .models import {struct_name}, {struct_name}Create, {struct_name}Update
from ..database import {struct_name}Model  # SQLAlchemy model


class SQLAlchemy{struct_name}DAO({struct_name}DAO):
    """SQLAlchemy implementation of {struct_name}DAO."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_by_id(self, entity_id: {pk_type}) -> Optional[{struct_name}]:
        """Find {table.name} by ID."""
        stmt = select({struct_name}Model).where({struct_name}Model.{pk.name if pk else 'id'} == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return {struct_name}.from_orm(model)
        return None
    
    async def find_all(self) -> List[{struct_name}]:
        """Find all {table.name}."""
        stmt = select({struct_name}Model)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [{struct_name}.from_orm(model) for model in models]
    
    async def create(self, entity: {struct_name}Create) -> {struct_name}:
        """Create a new {table.name}."""
        model = {struct_name}Model(**entity.dict())
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return {struct_name}.from_orm(model)
    
    async def update(self, entity_id: {pk_type}, entity: {struct_name}Update) -> Optional[{struct_name}]:
        """Update {table.name}."""
        update_data = entity.dict(exclude_unset=True)
        if not update_data:
            return await self.find_by_id(entity_id)
        
        stmt = (
            update({struct_name}Model)
            .where({struct_name}Model.{pk.name if pk else 'id'} == entity_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.find_by_id(entity_id)
    
    async def delete(self, entity_id: {pk_type}) -> bool:
        """Delete {table.name}."""
        stmt = delete({struct_name}Model).where({struct_name}Model.{pk.name if pk else 'id'} == entity_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
'''.strip()


class GoDAOGenerator:
    """Generates Go DAO code from database schema."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def generate_model(self, table: DatabaseTable) -> str:
        """Generate Go model struct."""
        package_name = self.service_name.lower().replace('-', '')
        
        fields = []
        for col in table.columns:
            field_type = col.go_type
            field_name = ''.join(word.capitalize() for word in col.name.split('_'))
            json_tag = col.name
            db_tag = col.name
            
            tags = f'`json:"{json_tag}" db:"{db_tag}"`'
            fields.append(f"\t{field_name} {field_type} {tags}")
        
        imports = []
        if any('time.Time' in col.go_type for col in table.columns):
            imports.append('\t"time"')
        if any('uuid.UUID' in col.go_type for col in table.columns):
            imports.append('\t"github.com/google/uuid"')
        
        import_block = ""
        if imports:
            import_block = f"import (\n{chr(10).join(imports)}\n)\n\n"
        
        return f'''
package {package_name}

{import_block}// {table.struct_name} represents a {table.name} in the system
type {table.struct_name} struct {{
{chr(10).join(fields)}
}}

// {table.struct_name}Create represents the data needed to create a {table.name}
type {table.struct_name}Create struct {{
  {chr(10).join([f'{chr(9)}{("".join(word.capitalize() for word in col.name.split("_")))} {col.go_type} `json:"{col.name}"`' for col in table.columns if not col.primary_key])}
}}

// {table.struct_name}Update represents the data that can be updated for a {table.name}
type {table.struct_name}Update struct {{
  {chr(10).join([f'{chr(9)}{("".join(word.capitalize() for word in col.name.split("_")))} *{col.go_type.lstrip("*")} `json:"{col.name},omitempty"`' for col in table.columns if not col.primary_key])}
}}
'''.strip()
    
    def generate_dao_interface(self, table: DatabaseTable) -> str:
        """Generate DAO interface for Go."""
        package_name = self.service_name.lower().replace('-', '')
        struct_name = table.struct_name
        pk = table.primary_key
        pk_type = pk.go_type if pk else 'uuid.UUID'
        
        return f'''
package {package_name}

import (
\t"context"
\t"github.com/google/uuid"
)

// {struct_name}DAO defines the interface for {table.name} data access operations
type {struct_name}DAO interface {{
\t// FindByID retrieves a {table.name} by its ID
\tFindByID(ctx context.Context, id {pk_type}) (*{struct_name}, error)
\t
\t// FindAll retrieves all {table.name}
\tFindAll(ctx context.Context) ([]*{struct_name}, error)
\t
\t// Create creates a new {table.name}
\tCreate(ctx context.Context, entity *{struct_name}Create) (*{struct_name}, error)
\t
\t// Update updates an existing {table.name}
\tUpdate(ctx context.Context, id {pk_type}, entity *{struct_name}Update) (*{struct_name}, error)
\t
\t// Delete deletes a {table.name} by its ID
\tDelete(ctx context.Context, id {pk_type}) error
}}
'''.strip()
    
    def generate_pg_dao_impl(self, table: DatabaseTable) -> str:
        """Generate PostgreSQL DAO implementation for Go."""
        package_name = self.service_name.lower().replace('-', '')
        struct_name = table.struct_name
        impl_name = f"pg{struct_name}DAO"
        pk = table.primary_key
        pk_type = pk.go_type if pk else 'uuid.UUID'
        
        return f'''
package {package_name}

import (
\t"context"
\t"database/sql"
\t"fmt"
\t
\t"github.com/google/uuid"
\t"github.com/jmoiron/sqlx"
)

// {impl_name} implements {struct_name}DAO using PostgreSQL
type {impl_name} struct {{
\tdb *sqlx.DB
}}

// New{struct_name}DAO creates a new PostgreSQL {struct_name}DAO
func New{struct_name}DAO(db *sqlx.DB) {struct_name}DAO {{
\treturn &{impl_name}{{
\t\tdb: db,
\t}}
}}

// FindByID retrieves a {table.name} by its ID
func (d *{impl_name}) FindByID(ctx context.Context, id {pk_type}) (*{struct_name}, error) {{
\tquery := `SELECT * FROM {table.name} WHERE {pk.name if pk else 'id'} = $1`
\t
\tvar entity {struct_name}
\terr := d.db.GetContext(ctx, &entity, query, id)
\tif err != nil {{
\t\tif err == sql.ErrNoRows {{
\t\t\treturn nil, nil
\t\t}}
\t\treturn nil, fmt.Errorf("failed to find {table.name} by ID: %w", err)
\t}}
\t
\treturn &entity, nil
}}

// FindAll retrieves all {table.name}
func (d *{impl_name}) FindAll(ctx context.Context) ([]*{struct_name}, error) {{
\tquery := `SELECT * FROM {table.name}`
\t
\tvar entities []{struct_name}
\terr := d.db.SelectContext(ctx, &entities, query)
\tif err != nil {{
\t\treturn nil, fmt.Errorf("failed to find all {table.name}: %w", err)
\t}}
\t
\t// Convert to pointer slice
\tresult := make([]*{struct_name}, len(entities))
\tfor i := range entities {{
\t\tresult[i] = &entities[i]
\t}}
\t
\treturn result, nil
}}

// Create creates a new {table.name}
func (d *{impl_name}) Create(ctx context.Context, entity *{struct_name}Create) (*{struct_name}, error) {{
\t// Implementation would depend on specific fields and requirements
\t// This is a basic template
\treturn nil, fmt.Errorf("create method not implemented")
}}

// Update updates an existing {table.name}
func (d *{impl_name}) Update(ctx context.Context, id {pk_type}, entity *{struct_name}Update) (*{struct_name}, error) {{
\t// Implementation would depend on specific fields and requirements
\t// This is a basic template
\treturn nil, fmt.Errorf("update method not implemented")
}}

// Delete deletes a {table.name} by its ID
func (d *{impl_name}) Delete(ctx context.Context, id {pk_type}) error {{
\tquery := `DELETE FROM {table.name} WHERE {pk.name if pk else 'id'} = $1`
\t
\t_, err := d.db.ExecContext(ctx, query, id)
\tif err != nil {{
\t\treturn fmt.Errorf("failed to delete {table.name}: %w", err)
\t}}
\t
\treturn nil
}}
'''.strip()


def generate_dao_from_schema(schema_file: str, output_dir: str, service_name: str, language: str):
    """Generate DAO code for the specified language."""
    generators = {
        'rust': RustDAOGenerator,
        'cpp': CppDAOGenerator,
        'python': PythonDAOGenerator,
        'go': GoDAOGenerator,
    }
    
    if language not in generators:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(generators.keys())}")
    
    generator = generators[language](service_name)
    
    # Read schema file
    with open(schema_file, 'r') as f:
        schema_content = f.read()
    
    # Parse tables (using the base parser from RustDAOGenerator)
    rust_generator = RustDAOGenerator(service_name)
    tables = rust_generator.parse_sql_schema(schema_content)
    
    output_path = Path(output_dir)
    
    if language == 'rust':
        generate_rust_dao_from_schema(schema_file, output_dir, service_name)
    
    elif language == 'cpp':
        for table in tables:
            models_dir = output_path / "models"
            dao_dir = output_path / "dao"
            models_dir.mkdir(parents=True, exist_ok=True)
            dao_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate model header
            with open(models_dir / f"{table.name}.hpp", 'w') as f:
                f.write(generator.generate_model(table))
            
            # Generate DAO interface
            with open(dao_dir / f"{table.name}_dao.hpp", 'w') as f:
                f.write(generator.generate_dao_interface(table))
            
            # Generate PostgreSQL implementation
            with open(dao_dir / f"pg_{table.name}_dao.hpp", 'w') as f:
                f.write(generator.generate_pg_dao_impl(table))
    
    elif language == 'python':
        for table in tables:
            table_dir = output_path / f"{table.name}"
            table_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate models
            with open(table_dir / "models.py", 'w') as f:
                f.write(generator.generate_model(table))
            
            # Generate DAO interface
            with open(table_dir / "dao.py", 'w') as f:
                f.write(generator.generate_dao_interface(table))
            
            # Generate SQLAlchemy implementation
            with open(table_dir / "sqlalchemy_dao.py", 'w') as f:
                f.write(generator.generate_sqlalchemy_dao(table))
            
            # Generate __init__.py
            with open(table_dir / "__init__.py", 'w') as f:
                f.write(f'''from .models import {table.struct_name}, {table.struct_name}Create, {table.struct_name}Update
from .dao import {table.struct_name}DAO
from .sqlalchemy_dao import SQLAlchemy{table.struct_name}DAO

__all__ = [
    "{table.struct_name}",
    "{table.struct_name}Create", 
    "{table.struct_name}Update",
    "{table.struct_name}DAO",
    "SQLAlchemy{table.struct_name}DAO",
]
''')
    
    elif language == 'go':
        package_name = service_name.lower().replace('-', '')
        
        for table in tables:
            # Generate model file
            with open(output_path / f"{table.name}.go", 'w') as f:
                f.write(generator.generate_model(table))
            
            # Generate DAO interface
            with open(output_path / f"{table.name}_dao.go", 'w') as f:
                f.write(generator.generate_dao_interface(table))
            
            # Generate PostgreSQL implementation
            with open(output_path / f"pg_{table.name}_dao.go", 'w') as f:
                f.write(generator.generate_pg_dao_impl(table))
    
    success(
        f"Generated {language.upper()} DAO structure for {len(tables)} tables in {output_dir}"
    )
