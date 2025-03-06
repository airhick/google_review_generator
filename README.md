# Google Review Generator

A tool to help post Google reviews for businesses by automating the review process.

## Features

- **Simple Review**: Post a 4-5 star review with random positive text
- **Custom Review**: Post a review with your own star rating and text
- **Direct Review URL**: Generate a direct URL for posting reviews
- **Google Places API Integration**: Extract business information and place ID using the Google Places API
- **Google Account Login**: Automatically logs in to Google before posting reviews
- **Debug Logs**: All operations are logged for troubleshooting

## Requirements

- Python 3.6+
- Chrome browser installed
- Required Python packages (see requirements.txt)
- Valid Google account credentials in accounts.yaml
- Google Places API key (for enhanced place ID extraction)

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Set up your Google account credentials in accounts.yaml:

```yaml
accounts:
  - username: your_email@gmail.com
    password: your_password
```

4. Set up your Google Places API key:
   - Copy the `.env.example` file to `.env`
   - Get an API key from [Google Cloud Platform](https://developers.google.com/maps/documentation/places/web-service/get-api-key)
   - Add your API key to the `.env` file:
   ```
   GOOGLE_PLACES_API_KEY=your_api_key_here
   ```

## Usage

Run the menu interface:

```bash
python review_menu.py
```

### Menu Options

1. **Set Business URL**: Enter the Google Maps URL for the business
2. **Generate Direct Review URL**: Create a direct URL for posting reviews
3. **Post Simple Review**: Post a 4-5 star review with random positive text
4. **Post Custom Review**: Post a review with your own star rating and text
5. **View Debug Logs**: View logs from previous operations
6. **Exit**: Close the application

### Workflow

1. Set Business URL
2. Generate Direct Review URL (optional but recommended)
3. Post a Simple or Custom Review
4. Check Debug Logs if any issues occur

## Google Account Login

The scripts now automatically log in to Google before posting reviews. This is required as Google only allows logged-in users to post reviews.

To set up your Google account:
1. Edit the `accounts.yaml` file
2. Add your Google account credentials
3. You can add multiple accounts if needed

Example accounts.yaml:
```yaml
accounts:
  - username: your_email@gmail.com
    password: your_password
  - username: another_email@gmail.com
    password: another_password
```

## Google Places API Integration

The application now uses the Google Places API to extract business information and get the place ID for generating direct review URLs. This provides a more reliable way to generate review URLs compared to extracting place IDs directly from URLs.

To use this feature:
1. Get a Google Places API key from [Google Cloud Platform](https://developers.google.com/maps/documentation/places/web-service/get-api-key)
2. Add your API key to the `.env` file
3. The application will automatically use the API to get the place ID when generating direct review URLs

If the API key is not provided or the API call fails, the application will fall back to the previous method of extracting place IDs directly from URLs.

## Debug Logs

The scripts save all logs to timestamped folders in the `debug_files` directory. This helps keep the main directory clean and organizes debugging information for each run.

Each debug folder contains:
- Error logs if any issues occur
- Screenshots of key steps in the process
- Login process screenshots for troubleshooting
- API responses from the Google Places API (when used)

## Direct Review URL

The direct review URL feature creates a URL that opens directly to the review form for a business. This is more reliable than trying to navigate to the review form from the business page.

To generate a direct review URL:
1. Set the business URL first
2. Select "Generate Direct Review URL" from the menu
3. The URL will be saved to `direct_review_url.txt`

The application now uses the following process to generate direct review URLs:
1. Extract the business name from the URL
2. Use the Google Places API to get the place ID for the business
3. Generate a direct review URL using the place ID
4. If the API call fails, fall back to extracting the place ID directly from the URL

## Troubleshooting

If you encounter issues:

1. Check the debug logs for error messages
2. Make sure Chrome is installed and not already running
3. Verify that the business URL is correct
4. Try generating a direct review URL if the regular URL doesn't work
5. Check if your Google Places API key is valid and has the necessary permissions

## Notes

- The scripts use undetected_chromedriver to avoid detection
- If undetected_chromedriver fails, it will fall back to standard Chrome driver
- The scripts will automatically use the direct review URL if available

## License

This project is for educational purposes only. Use responsibly and in accordance with Google's terms of service.

## Disclaimer

This tool is provided for educational purposes only. Use at your own risk. The authors are not responsible for any misuse or violations of terms of service. # google_review_generator
