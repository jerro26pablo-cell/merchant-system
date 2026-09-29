# Cloudinary Setup for Image Storage

## Why Cloudinary?
Render's free tier uses **ephemeral storage** - all uploaded files are deleted when you redeploy. To make images persist, we need cloud storage. Cloudinary offers a **free tier** that's perfect for this.

## Setup Steps:

### 1. Create a Cloudinary Account (Free)
1. Go to https://cloudinary.com/
2. Sign up for a free account
3. Go to your Dashboard
4. Copy your:
   - Cloud Name
   - API Key
   - API Secret
   - Cloudinary URL (from the top of the dashboard)

### 2. Add Environment Variables to Render
In your Render dashboard, add these environment variables:

```
USE_CLOUDINARY=True
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 3. Deploy
1. Push these changes to your repository
2. Render will automatically redeploy
3. Images will now be stored in Cloudinary and persist across deployments

## Free Tier Limits:
- 25GB of storage
- 25GB of bandwidth per month
- Perfect for starting out

## Alternative: Local Development
For local development, images will work with local storage. Only production needs Cloudinary.
