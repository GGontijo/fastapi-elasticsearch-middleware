from setuptools import setup, find_packages
  
setup( 
    name='fastapi_elasticsearch_middleware', 
    version='1.0.9', 
    url='https://github.com/GGontijo/fastapi-elasticsearch-middleware.git',
    description='Elasticsearch Logger Middleware for FastAPI',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    author='Gabriel Gontijo', 
    author_email='gabrieldercilio08@gmail.com', 
    packages=find_packages(), 
    keywords=['python', 'middleware', 'fastapi', 'elasticsearch', 'kibana', 'logstash', 'fastapi-middleware'],
    install_requires=[ 
        'fastapi', 
        'elasticsearch', 
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ]
) 