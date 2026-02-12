hbz.cdntools
============

This tool parses a HTML site and returns a list of found CSS and JS files from external Content Delivery Networks (CDN).
In addition <img> Tags are scanned for more Domains and collected in a file `hostnames.txt`. 

The module is installed by running:

.. code-block:: bash

    $ pip install -f https://dist.pubsys.hbz-nrw.de hbz.cdntools

Update a new version with

.. code-block:: bash

        $ pip install -f https://dist.pubsys.hbz-nrw.de -U hbz.cdntools


Dependencies like the `Requests`_ and `BeautifulSoup`_ libraries are installed automatically.

Usage:

.. code-block:: bash

    $ cdnparse -h

    usage: cdnparse [-h] [-a] [-k] [-n] [-c COOKIES] [-u USERAGENT] [-w WAIT] [-l LOGFILE] [--version] url

    CDN gathering

    positional arguments:
      url                   URL of website

    options:
      -h, --help            show this help message and exit
      -a, --all             include also local css/js
      -k, --keep            keep the downloaded HTML file
      -n, --no-check-certificate
                            do not validate SSL certificates
      -c COOKIES, --cookies COOKIES
                            Cookiestring
      -u USERAGENT, --useragent USERAGENT
                            User Agent (default: Google Chrome)
      -w WAIT, --wait WAIT  wait SECONDS seconds between requests
      -l LOGFILE, --logfile LOGFILE
                            Name of the logfile (default: cdnparse.log)
      --version             show program's version number and exit



Together with wpull the output of the `cdnparse` command can be used to harvest
a complete website including also external javascript or stylesheets from CDN servers.
The following bash script wraps wpull and cdnparse together. In a first step a
warc is created with only js and css files. Note that wpull is called non-recursive,
each wpull call should fetch just one single file, but put in the same warc file.

In the second step the actual webseite is recursively crawled and collected in
the warc from the first step.

.. code-block:: bash

    #!/bin/bash

    SITE=$1
    HOSTNAME=`echo $SITE | cut -d"/" -f3`
    TIMESTAMP=`date +"%Y%m%d%H%M%S"`
    NAME="$HOSTNAME-$TIMESTAMP"

    # CDNPARSE=/opt/regal/python3/bin/cdnparse
    CDNPARSE=cdnparse
    # WPULL=/opt/regal/python3/bin/wpull
    WPULL=wpull
    cdns=`$CDNPARSE -a  $SITE`

    echo "##### Gathering CSS and JS #####"
    for cdn in $cdns
    do
       $WPULL --warc-file $NAME \
              --no-check-certificate \
              --no-robots \
              --delete-after \
              --tries=5 \
              --waitretry=20 \
              --random-wait \
              --strip-session-id \
              --warc-append \
              --database $NAME.db \
              $cdn
    done

    echo "##### Gathering site #####"

    $WPULL --warc-file $NAME \
           --recursive \
           --tries=5 \
           --waitretry=20 \
           --random-wait \
           --link-extractors=javascript,html,css \
           --escaped-fragment \
           --strip-session-id \
           --no-host-directories \
           --page-requisites \
           --no-parent \
           --database $NAME.db \
           --no-check-certificate \
           --no-directories \
           --delete-after \
           --convert-links  \
           --span-hosts \
           --hostnames="$HOSTNAME" \
          $SITE


.. _Requests: https://pypi.org/project/requests/
.. _BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
