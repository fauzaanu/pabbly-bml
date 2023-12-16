
![](.README_images/header.png)

# Bank of Maldives Gateway for Pabbly Subscription Payments

## Table of Contents

1. [Introduction](#introduction)
2. [Deployment to Digital Ocean Apps Platform](#deployment-to-digital-ocean-apps-platform)
3. [Environment Variables](#environment-variables)
4. [Routes Explanation](#routes-explanation)
5. [Error Handling](#error-handling)

## Introduction

This application manages subscriptions and payments for products by interacting with Pabbly payment gateway and Bank of Maldives (BML) services. Optional integration with the Xperiencify learning management system is also offered.

## Deployment to Digital Ocean Apps Platform

Follow these steps to deploy the application on the Digital Ocean Apps Platform:

1. Visit [DigitalOcean](https://www.digitalocean.com/)
2. Navigate to the Apps section under "Create" in the top menu
3. Click on "Launch Your App"
4. Select your Github repository where your application is located
5. Set the branch and Project root directory, then click Next
6. Choose "Python" under "Environment"
7. Choose your Plan, Region then click Next
8. Add your Environment Variables (Remember not to expose any sensitive data)
9. Click "Launch Basic App" to deploy

## Environment Variables

Normally you would set these environment variables in a .env file. However, the Digital Ocean Apps Platform has a built-in way to set environment variables. You can set them in the "Environment Variables" section of the app settings.

```bash
BML_API_KEY = "The API key for Bank of Maldives."
PABBLY_USERNAME = "Pabbly API username."
PABBLY_PASSWORD = "Pabbly API password."
DEFAULT_REDIRECT_URL = "Fall back URL"
TELEGRAM_BOT_TOKEN = "Your Telegram bot token."
TELEGRAM_CHAT_ID = "Your Telegram chat ID."
XPERIENCIFY_API_KEY = "The API key for Xperiencify. This is optional. If not provided, the Xperiencify integration will be disabled."
```

### How to get BML API Key
You need to get the API key from BML Merchents platform. Please see the [bml connect docs](https://github.com/bankofmaldives/bml-connect) for more information.

### How to get Pabbly API Key
You need to get the API key from Pabbly. Please see the [pabbly api docs](https://www.apidocs.pabbly.com/) for more information.

### How to get Telegram Bot Token
Contact [@BotFather](https://t.me/botfather) on Telegram to create a new bot and get the token.

### How to get Telegram Chat ID
Contact [@jsondumpbot](https://t.me/jsondumpbot) on Telegram to get your chat ID. or a channels chat ID. To get the channels chatID just forward a message to the bot.

### How to get Xperiencify API Key
You need to get the API key from Xperiencify. Please see the [xperiencify api docs](https://howto.xperiencify.com/article.php?article=123) for more information.

## Routes Explanation

The application has several endpoints that it uses to handle different parts of the subscription and payment process:

**/pabbly**: Processes a user's subscription and initiates their payment.

**/hook**: Manages the response from the bank after a payment has been processed.

**/thankyou**: Gives feedback to the user after they've completed their payment, and either confirms their payment on both systems or gives an error.

## Error Handling

Error messages are sent to a specific Telegram chat using the Telegram Bot API. Go to DigitalOcean App Console logs section if an alert does not appear on telegram.