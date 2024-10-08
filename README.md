<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/maelen/piano_tools">
    <img src="docs/assets/piano-logo.jpg" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Piano Tools</h3>

  <p align="center">
    Generate Lessons for a midi piano/keyboard. And, useful scripts to use with my piano. 
    <br />
    ·
    <a href="https://github.com/maelen/piano_tools/issues">Report Bug</a>
    ·
    <a href="https://github.com/maelen/piano_tools/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

I started this project because I wanted to easily add piano lessons to my Casio piano. I have moved on to Synthesia now.
The xml2casiomidi.py script is still there but I have not tested it in a while. Currently the midi module splits hand parts using different tracks.
This probably does not work well with Casio piano that have the lesson mode.

The script to use to generate Synthesia lessons is xml2synthesia.py. The midi files should work with Pianobooster (Left and Right hand parts only).
And, I do not know if it works with Chordana and Casio Music Space.

xml2synthesia.py generates a midi file for each musicxml or Musescore file found in a folder and creates the metadata.synthesia file needed by Synthesia.

It can:
- separate the left and right hand parts
- Use the metadata to configure the title, subtitle, rank and difficulty
- Set bookmarks

The script requires one argument which is the folder where the music files can be found. Musescore must be in your search path.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

xml2synthesia.py is used from the command line.

Type: 
```sh
  ./xml2synthesia.py <Folder with music files>
```
The full list of arguments can be obtained by typing ./xml2synthesia.py -h


### Prerequisites

- Musescore 3
- Python 3.6+
- Python modules mido and multitimer

Scripts have been tested on Linux but they should work on other platforms.


### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/maelen/piano_tools.git
   ```
2. Download and install Musescore 3

3. Add Musescore to your search path (Not needed on Linux)

4. Install python modules 
   ```sh
   pip3 install mido
   pip3 install multitimer
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Marie-Josee Blais

Open an issue if you wish to contact me. I'm trying to cut down on spam :) You can also reach me with [Linkedin][linkedin-url].

Project Link: [https://github.com/maelen/piano_tools](https://github.com/maelen/piano_tools)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/maelen/piano_tools.svg?style=for-the-badge
[contributors-url]: https://github.com/maelen/piano_tools/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/maelen/piano_tools.svg?style=for-the-badge
[forks-url]: https://github.com/maelen/piano_tools/network/members
[stars-shield]: https://img.shields.io/github/stars/maelen/piano_tools.svg?style=for-the-badge
[stars-url]: https://github.com/maelen/piano_tools/stargazers
[issues-shield]: https://img.shields.io/github/issues/maelen/piano_tools.svg?style=for-the-badge
[issues-url]: https://github.com/maelen/piano_tools/issues
[license-shield]: https://img.shields.io/github/license/maelen/piano_tools.svg?style=for-the-badge
[license-url]: https://github.com/maelen/piano_tools/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/marie-josee-blais-8000731
[product-screenshot]: images/screenshot.png
