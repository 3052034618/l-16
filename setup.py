from setuptools import setup, find_packages

setup(
    name="carbon-calc",
    version="1.0.0",
    description="碳减排项目评估命令行工具",
    author="Carbon Calc Team",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "carbon-calc = carbon_calc.cli:main",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
