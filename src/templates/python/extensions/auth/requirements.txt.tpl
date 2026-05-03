# Authentication extension requirements
# Adds JWT authentication and password hashing support

# JWT handling
python-jose[cryptography]>=3.5,<4

# Password hashing
passlib[bcrypt]>=1.7,<2

# Form data handling for login endpoints
python-multipart>=0.0.20,<1
