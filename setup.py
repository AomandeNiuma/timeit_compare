from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='timeit_compare',
    version='1.1.2',
    py_modules=['timeit_compare'],
    license='MIT',
    python_requires='>=3.6.0',
    description='A method based on timeit that can help you to call '
                'timeit.timeit for several statements and provide '
                'comparison results.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Liu Wei',
    author_email='23S112099@stu.hit.edu.cn',
    maintainer='Liu Wei',
    maintainer_email='23S112099@stu.hit.edu.cn',
    url='https://github.com/AomandeNiuma/timeit_compare',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ]
)
