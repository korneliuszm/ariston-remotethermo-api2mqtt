import setuptools

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setuptools.setup(
    name="ariston-remotethermo-api2mqtt", 
    version="0.0.1",
    license='MIT',
    author="smarthomepch",
    author_email="smarthomepch@gmail.com",
    description="Transfer Ariston NET data to MQTT broker",
    long_description=README + '\n\n' + HISTORY,
    long_description_content_type="text/markdown",
    url="https://github.com/smarthomepch/ariston-remotethermo-api2mqtt",
    download_url='https://pypi.org/project/ariston-remotethermo-api2mqtt/',
    packages=setuptools.find_packages(),
    keywords=['Ariston NET', 'Remotethermo', 'Ariston', 'MQTT'],
    python_requires='>=3.6',
)