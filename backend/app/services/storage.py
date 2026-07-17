import logging
import os
from typing import Any
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger("app.services.storage")


class StorageService:
    """
    Decoupled storage provider interfacing with S3-compatible endpoints (MinIO).
    Includes automatic bucket bootstrapping and local filesystem fallbacks.
    """
    def __init__(self) -> None:
        endpoint = settings.MINIO_ENDPOINT
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            endpoint = f"http://{endpoint}"

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1"
        )
        self.local_fallback_dir = os.path.join(os.getcwd(), "scratch", "storage_fallback")

    async def init_bucket(self, bucket_name: str = settings.MINIO_BUCKET_NAME) -> None:
        """
        Initializes the target S3 bucket if it doesn't already exist.
        """
        try:
            # Run check synchronously in an executor or execute directly since connection is fast
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"MinIO bucket '{bucket_name}' already exists.")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            # 404 means bucket does not exist, we create it
            if error_code == "404":
                try:
                    self.s3_client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Successfully created MinIO bucket '{bucket_name}'.")
                except Exception as ex:
                    logger.error(f"Failed to create MinIO bucket: {ex}.")
            else:
                logger.error(f"MinIO connection check failed: {e}. Running in local storage mode.")
        except Exception as e:
            logger.error(f"Could not connect to MinIO on boot: {e}. Running in local fallback mode.")

    async def upload_file(
        self,
        file_data: bytes,
        file_name: str,
        bucket_name: str = settings.MINIO_BUCKET_NAME
    ) -> bool:
        """
        Uploads file bytes to the S3 bucket. Falls back to writing to local disk
        if MinIO is offline.
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=file_name,
                Body=file_data,
                ContentType="application/pdf"
            )
            logger.info(f"Successfully uploaded '{file_name}' to MinIO bucket '{bucket_name}'.")
            return True
        except Exception as e:
            logger.warning(
                f"MinIO upload failed: {e}. Saving proposal PDF to local filesystem fallback."
            )
            # Safe local filesystem fallback
            try:
                os.makedirs(self.local_fallback_dir, exist_ok=True)
                local_path = os.path.join(self.local_fallback_dir, file_name)
                with open(local_path, "wb") as f:
                    f.write(file_data)
                logger.info(f"Saved file locally at: {local_path}")
                return True
            except Exception as io_err:
                logger.error(f"Local storage fallback failed: {io_err}")
                return False

    async def get_presigned_url(
        self,
        file_name: str,
        expires_in: int = 3600,
        bucket_name: str = settings.MINIO_BUCKET_NAME
    ) -> str:
        """
        Generates a secure, temporary pre-signed download link. Returns local
        rel-path link if utilizing local filesystem fallback.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": file_name},
                ExpiresIn=expires_in
            )
            return url
        except Exception:
            logger.warning("Could not generate pre-signed URL. Returning local fallback link.")
            # Returns a link pointing to the local scratch path
            local_path = os.path.join(self.local_fallback_dir, file_name)
            return f"file:///{local_path.replace(os.sep, '/')}"
