from setuptools import setup

setup(
    name='ngawest2',
    version='0.0.1',
    description='A Python library for elegant data visualization',
    author='Feng Wang, Jian Shi',
    license='GPL v3.0',
    url='https://github.com/Caltech-geoquake/ngawest2',
    packages=['ngawest2'],
    classifiers=['Intended Audience :: Science/Research',
                'Topic :: Scientific/Engineering',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3.5',
                'Programming Language :: Python :: 3.6',
                'Programming Language :: Python :: 3.7',
    ],
    install_requires=['numpy>=1.11.0',
                      'matplotlib',
    ],
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    include_package_data=True,
)
