<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>

<h1>ComicMetaLink (CML)</h1>

<p>ComicMetaLink (CML) is a Python script developed to organize and generate symlinks for comic files (.cbz, .cbr, .pdf) using metadata extracted from ComicInfo.xml files. In cases where metadata is unavailable, it defaults to using directory and file names to create symlinks. The script identifies duplicates and only creates symlinks for the highest quality version of each comic, thus preventing duplicate displays in Komga or other comic readers.</p>

<h2>Features</h2>
<ul>
    <li>Extracts metadata from <code>ComicInfo.xml</code>.</li>
    <li>Creates symlinks based on extracted metadata.</li>
    <li>Falls back to directory and file names when <code>ComicInfo.xml</code> is not found.</li>
    <li>Get rid of dupes by not reflinking the same comic several times.</li>
    <li>Keeps the highest possible resolution when reflinking a comic.</li>  
    <li>Cleans up obsolete symlinks.</li>
    <li>Sends processing statistics to a specified Discord webhook.</li>
</ul>

<h2>Prerequisites</h2>
<ul>
    <li>Python 3.6+</li>
    <li>Required Python packages:
        <ul>
            <li><code>requests</code></li>
            <li><code>unidecode</code></li>
        </ul>
    </li>
</ul>

<h2>Installation</h2>
<p>Install the required Python packages using pip:</p>
<pre><code>pip install requests unidecode</code></pre>

<h2>Usage</h2>
<p>To run the script, use the following command:</p>
<pre><code>python comicmetalink.py --source <source_directories> --dest <destination_directory> --webhook <discord_webhook_url></code></pre>

<h3>Parameters</h3>
<ul>
    <li><code>--source</code>: List of source directories to process.</li>
    <li><code>--dest</code>: Destination root directory for symlinks.</li>
    <li><code>--webhook</code>: Discord webhook URL for notifications.</li>
</ul>
<p>Alternatively, the script can be edited to add source, destination directories and the webhook, in which case, there is no need to use parameters at all.</p>
<h3>Example</h3>
<pre><code>python comicmetalink.py --source /path/to/your/comics/ --dest /path/to/your/reflinks/ --webhook https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX</code></pre>

</body>
</html>

