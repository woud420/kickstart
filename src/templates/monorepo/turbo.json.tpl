{
  "$schema": "https://turborepo.org/schema.json",
  "globalDependencies": [".env"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**", "public/build/**"]
    },
    "clean": {
      "cache": false
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "outputLogs": "new-only"
    },
    "test": {
      "dependsOn": ["^typecheck"],
      "outputLogs": "new-only"
    },
    "typecheck": {
      "dependsOn": ["^typecheck"],
      "outputLogs": "new-only"
    }
  }
}
