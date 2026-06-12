# Authentication extension requirements
# Adds JWT authentication and password hashing support

# JWT handling
python-jose[cryptography]>=3.5,<4

# Password hashing (bcrypt directly; passlib is unmaintained and breaks with bcrypt>=4.1)
bcrypt>=4.1,<6

# Form data handling for login endpoints
python-multipart>=0.0.20,<1
