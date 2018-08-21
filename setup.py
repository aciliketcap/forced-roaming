import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="forced_roaming",
    version="0.0.1",
    author="Sinan Akpolat",
    description="WiFi management library to enforce roaming under specified"
    "rules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aciliketcap/forced-roaming",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Networking"
    ],
)
