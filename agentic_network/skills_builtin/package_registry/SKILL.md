# Package Registry

Reads metadata from fixed PyPI or npm endpoints after explicit network
permission and Approval Center review.

The lookup action accepts ecosystem (pypi or npm) and a validated package name.
It returns bounded metadata and available versions. It cannot download
archives, invoke package managers, or install dependencies.
