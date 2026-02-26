from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    port: int = Field(5001, validation_alias="PORT")
    mongodb_uri: str = Field(..., validation_alias="MONGODB_URI")
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    
    google_client_id: str = Field(..., validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., validation_alias="GOOGLE_CLIENT_SECRET")
    google_callback_url: str = Field(..., validation_alias="GOOGLE_CALLBACK_URL")
    
    session_secret: str = Field(..., validation_alias="SESSION_SECRET")
    
    cloudinary_cloud_name: str = Field(..., validation_alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(..., validation_alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(..., validation_alias="CLOUDINARY_API_SECRET")
    
    frontend_url: str = Field("http://localhost:5173", validation_alias="FRONTEND_URL")
    
    node_env: str = Field("development", validation_alias="NODE_ENV")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
