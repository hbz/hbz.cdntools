Changelog
=========

hbz.cdntools 0.7 (2025-04-11)
-----------------------------

* Domains from link with rel dns-prefetch or preconnect considered as external --hostname

hbz.cdntools 0.6 (2025-01-27)
-----------------------------

* extract image urls etc from stylesheets
* new flag to ignore invalid SSL certificates: `-n, --no-check-certificate`
* fix: hostnames no longer appended to hostname.txt for subsequent crawls

hbz.cdntools 0.5 (2024-07-01)
-----------------------------

* new flag to specify cookies and user agent
* collect external Domains in hostnames.txt


hbz.cdntools 0.4 (2024-01-26)
-----------------------------

* some Plones sites include css files via @import, e.g.
  <style type="text/css" media="screen"><!-- @import url(https://www.example.org/style.css); --></style>
  These are now parsed as well
