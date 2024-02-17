from pathlib import Path
import sys
from setuptools import find_packages, setup

this_directory = Path(__file__).parent
if __name__ == "__main__":
    this_directory = Path(__file__).parent
    long_description = (this_directory / "README.md").read_text()
    setup(
        name="selfcord.py",
        packages=find_packages(
            include=[
                "selfcord",
                "selfcord.api",
                "selfcord.utils",
                "selfcord.models",
                "selfcord.api.voice",
            ]
        ),
        version="1.0.2",
        description="A Discord API wrapper designed for selfbots!",
        readme="README.md",
        author="Shell",
        extras_require={
            "voice": ["pynacl==1.5.0", "opuslib==3.0.1"],
            "linux": ["uvloop==0.17.0"],
            "windows": ["winloop==0.1.0"]
        },
        license="MIT",
        install_requires=[
            "aiohttp==3.8.5",
            "aioconsole==0.3.3",
            "websockets==10.1",
            "ujson==5.7.0",
            "aiofiles==0.8.0",
            "requests==2.31.0",
            "uvloop==0.17.0"
        ] if sys.platform == "linux" else 
        [
            "aiohttp==3.8.5",
            "aioconsole==0.3.3",
            "websockets==10.1",
            "ujson==5.7.0",
            "aiofiles==0.8.0",
            "requests==2.31.0",
            "winloop==0.1.0"
        ],
        setup_requires=["pytest-runner"],
        tests_require=["pytest"],
        test_suite="tests",
        keywords=["selfbot", "discord", "discordapi", "discordwrapper"],
        long_description=long_description,
        url="https://github.com/OmegaDevStudio/Selfcord",
        long_description_content_type="text/markdown",
    )
