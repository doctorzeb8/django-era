from setuptools import setup, find_packages

setup(
    name='django-era',
    version='1.1.3',
    author='doctorzeb8',
    author_email='doctorzeb8@gmail.com',
    url='https://github.com/doctorzeb8/django-era',
    description='django app that introduces some architectural solutions',
    long_description='so what`s a problem? let`s do it quick!',
    license='MIT',

    packages = find_packages(),
    package_data={'era': ['*.html', '*.css', '*.js']},
    include_package_data = True,

    install_requires=[
        'Django==1.8.2',
        'django-bower==5.0.4',
        'django-classy-tags==0.6.1'],
    extras_require={
        'dev': [
            'django-debug-toolbar==1.3.0',
            'ipdb==0.8',
            'ipython==3.0.0']},

    keywords='django framework cbv components react',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django'])
