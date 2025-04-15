import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service for uploading files to Cloudinary.
    """

    def __init__(self, cloud_name, api_key, api_secret):
        """
        Initialize the Cloudinary configuration with the given credentials.

        Args:
            cloud_name (str): Cloudinary cloud name.
            api_key (str): Cloudinary API key.
            api_secret (str): Cloudinary API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Upload a file to Cloudinary and return its public URL.

        Args:
            file (UploadFile): File to be uploaded.
            username (str): Username used to generate a unique public_id.

        Returns:
            str: URL of the uploaded file on Cloudinary.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
