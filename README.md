
![](.README_images/header.png)

# Bank of Maldives Gateway for Pabbly Subscription Payments

## Table of Contents

1. [Introduction](#introduction)
2. [Deployment to Digital Ocean Apps Platform](#deployment-to-digital-ocean-apps-platform)
3. [Environment Variables](#environment-variables)
    * [How to get BML API Key](#how-to-get-bml-api-key)
    * [How to get Pabbly API Key](#how-to-get-pabbly-api-key)
    * [How to get Telegram Bot Token](#how-to-get-telegram-bot-token)
    * [How to get Telegram Chat ID](#how-to-get-telegram-chat-id)
    * [How to get Xperiencify API Key](#how-to-get-xperiencify-api-key)
4. [Routes Explanation](#routes-explanation)
    * [Route Handlers](#route-handlers)
    * [Application Functions](#application-functions)
5. [Error Handling](#error-handling)

## Introduction

This application manages subscriptions and payments for products by interacting with Pabbly payment gateway and Bank of Maldives (BML) services. Optional integration with the Xperiencify learning management system is also offered.
![](.README_images/project_overview.png)

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

### Route Handlers
![](.README_images/routes.png)

1. **'/' (GET)**: The root route returns some logging data of the incoming request and then redirects to the default redirect URL. As soon as the app is initiated, the message “App started” will be sent as well.

2. **'/pabbly' (GET)**: It processes a customer's payment through a Pabbly-hosted page. The Pabbly API returns invoice data that are then used to form a payload for the Bank of Maldives (BML) API. This payload gets sent back to the BML instance, which responds with a payment URL. Customer then gets redirected to that payment URL to finalize their payment.

3. **'/hook' (POST)**: This is a webhook endpoint that is triggered by the Bank of Maldives when they send a POST request on payment completion. This function checks the status of the transaction, then processes and records it if it has been confirmed.

4. **'/thankyou' (GET)**: Followed by a successful payment, a GET request is made to this route. The handler function checks if the payment approval from BML matches the state of the payment. If the payment is confirmed, the handler records the payment in the Pabbly system, and creates a redirect link that sends the customer to a thank you page. If the payment is cancelled by the bank, an error is logged and the customer is redirected to a default URL.


## Application Functions (For Developers)

1. **error_logging(message: str) -> bool**: This method logs errors to a specified Telegram chat through the Telegram Bot API.

2. **process_subscription_pabbly()**: This function retrieves the transaction and customer details from Pabbly's payment gateway, and then structures the retrieved data into a format that the BML payment gateway can understand.

3. **record_payment(transaction_id: str) -> str**: Queries the transaction to get the local ID and product ID, and then checks the invoice status. If invoice status is 'success', it returns product ID. If invoice status is 'created', this function records the payment and returns product ID.

4. **bml_hook()**: This is the method mapped for BML's webhook endpoint. It gets the transaction ID, queries BML to get transaction information. If all checks out, it records the payment and then returns the result.

5. **thankyou()**: This function handles the /thankyou.php route and handles transaction outcome (CONFIRMED or CANCELLED), and redirects the user accordingly.

These functions are created with modular programming practices in mind by grouping the related functions into corresponding namespaces. This makes the code base easier to maintain and develop.

## Error Handling

Error messages are sent to a specific Telegram chat using the Telegram Bot API. Go to DigitalOcean App Console logs section if an alert does not appear on telegram.

