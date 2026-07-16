"""Optional two-instance Redis load-coordination workshop.

Import the explicit ``codec``, ``observer``, ``service``, or ``application``
submodule only after installing the ``redis-coordination`` extra. Keeping this
package initializer dependency-free preserves default pytest collection.
"""
