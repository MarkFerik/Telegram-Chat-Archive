Telegram Chat Archive Generator — A private Python-based toolkit for locally exporting, structuring, and transforming Telegram chats into a clean, interactive web archive. Designed to securely manage chat history and media with full privacy and custom local hosting capabilities

To get api_id and api_hash for Telegram (for example, to run your own scripts, bots, or client), you need to register an application on the official developer website.

Here is a simple step-by-step guide on how to do this:

    Go to the official website my.telegram.org in your browser.

    Enter the phone number linked to your Telegram account (in international format, e.g., +380... or another) and click Next.

    An official service message with a confirmation code will arrive inside the Telegram application itself. Copy this code and enter it on the website, then click Sign In.

    After logging in, select the API development tools section.

    Fill out the simple form to create a new application:

        App title: Enter any name (for example, MyTelegramArchive or just My App).

        Short name: A short name using Latin characters (for example, myarchiveapp).

        The remaining fields (URL, Platform) can be left blank or filled out as desired.

    Click the Create application button at the bottom of the form.

After this, the created application will appear on the page, displaying two main parameters:

    api_id (usually a set of 7–8 digits)

    api_hash (a long string of letters and numbers)

Important Security

Never, under any circumstances, share your api_hash and api_id! They can be used to gain full access to your Telegram account. Keep this data secret.
