from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='smartbox',
      version="0.0.1",
      author="Graham Bennett",
      author_email="graham@grahambennett.org",
      description="Python API to control heating 'smart boxes'",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/graham33/smartbox",
      py_modules=['smartbox'],
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
      install_requires=['Click', 'requests'],
      entry_points='''
      [console_scripts]
      smartbox=smartbox:smartbox
      ''')
