To run project;
    -Open docker postgres container
    -uvicorn app.main:app --port 8000 --reload

Current Position:
    Core:
        Database:
            -Created database and tables from models.
            -With docker we created postgres container. (5433:5432) port issue solved.
            -Using alembic for orm.
        Security:
            -Verify password, Hash password, Creating access token, Getting Current User implemented.
            -We can login,register and safely store password with that. Also we can verify current user with token.
        Config:
            -This file only responsible for Global enviroments like DATABASE_URL also algorithm and api secrets.
            
    Auth:
        API:
            -Login(token) and register api's created
            -We can succesfully creating user in db and login.
            -Creating access_token for 8 hour.
            TODO:Companies
        SCHEMAS:
            -user schema including email ,password.
            - UserResponse schema including id,is_active,created_at,updated_at areas.
            -Token Schema access_token,token_type (bearer)
            TODO:Companies
        CRUD:
            -Created functionalites as controller on api endpoints.
            -get_user_by_email, create_user,get_user functions created.
            -We can getting user by email and creating user also access to specific user.
            TODO:Companies

TODO's
    - Refresh token mekanizması kullanılabilir. şu anlık 8 saatlik bir token veriyoruz
    -
    