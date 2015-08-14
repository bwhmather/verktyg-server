`Verktyg Server <verktyg_server_>`_
====================================

|build-status| |coverage|



Examples
--------

Basic
~~~~~

.. code:: python
    from verktyg_server import make_socket, make_server


    def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)

            return [
                ("%s: %r\n" % (key, value)).encode('utf-8')
                for key, value in environ.items()
            ]


    server = make_server(make_socket('localhost', 8080), application)
    server.run_forever()


Basic HTTPS
~~~~~~~~~~~

.. code:: python
    from verktyg_server import make_socket, make_server, load_ssl_context


    def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)

            return [
                ("%s: %r\n" % (key, value)).encode('utf-8')
                for key, value in environ.items()
            ]


    ssl_context = ssl.load_ssl_context(
        '/path/to/certificate.pem', '/path/to/key.pem'
    )
    sock = make_socket('localhost', 8080, ssl_context=ssl_context)
    server = make_server(sock, application)
    server.run_forever()


Bugs
----

Please post any problems or feature requests using the `issue tracker <issues_>`_


.. |build-status| image:: https://travis-ci.org/bwhmather/verktyg-server.png?branch=master
    :target: http://travis-ci.org/bwhmather/verktyg-server
    :alt: Build Status
.. |coverage| image:: https://coveralls.io/repos/bwhmather/verktyg-server/badge.png?branch=develop
    :target: https://coveralls.io/r/bwhmather/verktyg-server?branch=develop
    :alt: Coverage
.. _verktyg: https://github.com/bwhmather/verktyg
.. _verktyg_server: https://github.com/bwhmather/verktyg-server
.. _issues: https://github.com/bwhmather/verktyg-server/issues
