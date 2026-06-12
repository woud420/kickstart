#![allow(dead_code)]

use jsonwebtoken::{
    Algorithm, DecodingKey, EncodingKey, Header, Validation, decode, encode, errors::Error,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub exp: usize,
    pub iss: String,
}

pub fn create_token(
    subject: &str,
    secret: &str,
    issuer: &str,
    expires_at: usize,
) -> Result<String, Error> {
    let claims = Claims {
        sub: subject.to_string(),
        exp: expires_at,
        iss: issuer.to_string(),
    };

    encode(
        &Header::new(Algorithm::HS256),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
}

pub fn verify_token(token: &str, secret: &str, issuer: &str) -> Result<Claims, Error> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.set_issuer(&[issuer]);

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &validation,
    )?;
    Ok(token_data.claims)
}

#[cfg(test)]
mod tests {
    use super::*;

    // 2100-01-01T00:00:00Z: far enough out that expiry never flakes a test.
    const FAR_FUTURE: usize = 4102444800;

    #[test]
    fn token_roundtrip_preserves_claims() -> Result<(), Error> {
        let token = create_token("user-123", "test-secret", "issuer", FAR_FUTURE)?;
        let claims = verify_token(&token, "test-secret", "issuer")?;

        assert_eq!(claims.sub, "user-123");
        assert_eq!(claims.iss, "issuer");
        Ok(())
    }

    #[test]
    fn wrong_secret_is_rejected() -> Result<(), Error> {
        let token = create_token("user-123", "test-secret", "issuer", FAR_FUTURE)?;

        assert!(verify_token(&token, "another-secret", "issuer").is_err());
        Ok(())
    }

    #[test]
    fn wrong_issuer_is_rejected() -> Result<(), Error> {
        let token = create_token("user-123", "test-secret", "issuer", FAR_FUTURE)?;

        assert!(verify_token(&token, "test-secret", "another-issuer").is_err());
        Ok(())
    }
}
