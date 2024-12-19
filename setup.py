from setuptools import setup, find_packages

setup(
    name='ktg_chat_django',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[


        'Django==4.2.5',
        'djangorestframework==3.14.0',

    ],
    description='A reusable Django app for managing chat in django functionality',

    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Kayak Technology Group',
    author_email='info@kayaktechgroup.com',
    url='https://github.com/KayakTech/ktg_storage',
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12.7',
        'License :: OSI Approved :: MIT License',
    ],
)
