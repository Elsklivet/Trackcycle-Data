# Trackcycle Data Analysis

This repository hosts data analysis scripts and simulation scripts to evaluate the efficacy of implementations for the [Trackcycle](https://github.com/Elsklivet/Trackcycle) project, including (1) power saved, (2) accuracy, and (3) sensitivity/parameter analysis.

## [Trackcycle](https://github.com/Elsklivet/Trackcycle)

Trackcycle is a mobile application designed to track bicycle trips while minimizing device power usage, without accepting major accuracy sacrifices. The application uses duty-cycling triggered by using a combination of on-device inertial measurement unit (IMU) and magnetometer sensors to detect when bicycle riders have veered off of a straight, estimable path. It is written in the Kotlin programming language, targetting the Android operating system at API level 31. In addition to the core goal of maintaining minimal power usage/maximal accuracy, goals of the project at this time include to improve the duty-cycling mechanism's accuracy in detecting turns so that the GPS remains off more often than it currently does, enhance data collection used to evaluate power saving and accuracy, and to improve path estimation during off time.  

## Contributing

For detailed contributing information, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Copyright Notices

Some of the code included in this project draws inspiration from several sources, including other academic projects (with express permission), as well as internet sources and blogs such as [Janakiev's Blog](https://janakiev.com/blog/gps-points-distance-python/) (thanks for the idea to implement Haversine's formula). We've done our best to attribute appropriate sources for code included in the project. If you feel that your work has been incorrectly attributed per the appropriate license, please contact @Elsklivet at <gmh33@pitt.edu> or <gavinmajetich@gmail.com>. Additionally, this project is intended only for academic research, and not resale, so most uses should fall under [fair use](https://www.copyright.gov/fair-use/) by nature of the project. Still, I will do my best to remedy any attribution or copyright problems immediately. 

Any original code in this project is licensed under the [GNU GPL v3](./GPL-LICENSE.txt).

For contributors, it is **extremely important** that code you find is properly attributed and that copyrights are not infringed. Any contributions including code that is improperly attributed, in violation of the original work's copyright, or uses a copyright that is not permissive enough will be **rejected**.

## References

[1] Janakiev, N. (2018, March 9). “Calculate Distance Between GPS Points in Python.” *Parametric Thoughts*. Retrieved September 8, 2022, from https://janakiev.com/blog/gps-points-distance-python/.