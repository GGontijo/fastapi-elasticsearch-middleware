from setuptools import setup, find_packages
  
setup( 
    name='fastapi_elasticsearch_middleware', 
    version='0.1.0', 
    url='https://github.com/GGontijo/fastapi-elasticsearch-middleware.git',
    description='Elasticsearch Logger Middleware for FastAPI',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Gabriel Gontijo', 
    author_email='gabrieldercilio08@gmail.com', 
    packages=find_packages(), 
    install_requires=[ 
        'fastapi', 
        'elasticsearch', 
    ], 
) 