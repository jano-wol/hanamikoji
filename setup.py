import setuptools

VERSION = '1.1.0'

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hanamikojizero",
    version=VERSION,
    author="Janos Wolosz",
    author_email="jjjkamu@gmail.com",
    description="Hanamikoji AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jano-wol/hanamikoji",
    license='Apache License 2.0',
    keywords=["Hanamikoji", "DouZero", "AI", "Reinforcment Learning", "RL", "Torch", "Poker"],
    packages=setuptools.find_packages(),
    install_requires=[
        'torch',
        'rlcard'
    ],
    requires_python='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
