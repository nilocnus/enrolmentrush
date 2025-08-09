# utils.py 
import random


colours = {
    "background": "lightgray",
    "foreground": "white",
    "course_container": "gray",
    "course_text": "white",
    "label_container": "gray",
    "player_name_foreground": "blue"
}

cmpt_courses = {
    "CMPT 102": {
        "name": "Introduction to Scientific Computer Programming",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 105W": {
        "name": "Social Issues and Communication Strategies in Computing Science",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 106": {
        "name": "Applied Science, Technology and Society",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 110": {
        "name": "Programming in Visual Basic",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 115": {
        "name": "Exploring Computer Science",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 118": {
        "name": "Special Topics in Computer and Information Technology",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 120": {
        "name": "Introduction to Computing Science and Programming I",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 125": {
        "name": "Introduction to Computing Science and Programming II",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 128": {
        "name": "Introduction to Computing Science and Programming for Engineers",
        "points": 0,
        "available_seats": 1
    },
    "CMPT 129": {
        "name": "Introduction to Computing Science and Programming for Mathematics and Statistics",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 130": {
        "name": "Introduction to Computer Programming I",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 135": {
        "name": "Introduction to Computer Programming II",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 166": {
        "name": "An Animated Introduction to Programming",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 201": {
        "name": "Systems Programming",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 210": {
        "name": "Probability and Computing",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 213": {
        "name": "Object Oriented Design in Java",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 218": {
        "name": "Special Topics in Computing Science",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 225": {
        "name": "Data Structures and Programming",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 263": {
        "name": "Introduction to Human-Centered Computing",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 272": {
        "name": "Web I - Client-side Development",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 275": {
        "name": "Software Engineering I",
        "points": 0,
        "available_seats": 1
    },
    "CMPT 276": {
        "name": "Introduction to Software Engineering",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 295": {
        "name": "Introduction to Computer Systems",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 300": {
        "name": "Operating Systems I",
        "points": 0,
        "available_seats": 1
    },
    "CMPT 303": {
        "name": "Operating Systems",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 305": {
        "name": "Computer Simulation and Modelling",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 307": {
        "name": "Data Structures and Algorithms",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 308": {
        "name": "Computability and Complexity",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 310": {
        "name": "Introduction to Artificial Intelligence",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 318": {
        "name": "Special Topics in Computing Science",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 320": {
        "name": "Social Implications - Computerized Society",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 340": {
        "name": "Biomedical Computing",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 353": {
        "name": "Computational Data Science",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 354": {
        "name": "Database Systems I",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 361": {
        "name": "Introduction to Visual Computing",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 362": {
        "name": "Mobile Applications Programming and Design",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 363": {
        "name": "User Interface Design",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 365": {
        "name": "Multimedia Systems",
        "points":2,
        "available_seats": 1
    },
    "CMPT 371": {
        "name": "Data Communications and Networking",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 372": {
        "name": "Web II - Server-side Development",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 373": {
        "name": "Software Development Methods",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 376W": {
        "name": "Professional Responsibility and Technical Writing",
        "points": 4,
        "available_seats": 1
    },
    "CMPT 379": {
        "name": "Principles of Compiler Design",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 383": {
        "name": "Comparative Programming Languages",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 384": {
        "name": "Symbolic Computing",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 400": {
        "name": "3D Computer Vision",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 403": {
        "name": "System Security and Privacy",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 404": {
        "name": "Cryptography and Cryptographic Protocols",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 405": {
        "name": "Design and Analysis of Computing Algorithms",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 406": {
        "name": "Computational Geometry",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 407": {
        "name": "Computational Complexity",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 409": {
        "name": "Special Topics in Theoretical Computing Science",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 410": {
        "name": "Machine Learning",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 411": {
        "name": "Knowledge Representation",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 412": {
        "name": "Computer Vision",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 413": {
        "name": "Computational Linguistics",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 415": {
        "name": "Special Research Projects",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 416": {
        "name": "Special Research Projects",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 417": {
        "name": "Intelligent Systems",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 419": {
        "name": "Special Topics in Artificial Intelligence",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 420": {
        "name": "Deep Learning",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 426": {
        "name": "Practicum I",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 427": {
        "name": "Practicum II",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 428": {
        "name": "Practicum III",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 429": {
        "name": "Practicum IV",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 430": {
        "name": "Practicum V",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 431": {
        "name": "Distributed Systems",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 433": {
        "name": "Embedded Systems",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 441": {
        "name": "Computational Biology",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 450": {
        "name": "Computer Architecture",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 454": {
        "name": "Database Systems II",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 456": {
        "name": "Information Retrieval and Web Search",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 459": {
        "name": "Special Topics in Database Systems",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 461": {
        "name": "Computational Photography and Image Manipulation",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 464": {
        "name": "Geometric Modelling in Computer Graphics",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 466": {
        "name": "Animation",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 467": {
        "name": "Visualization",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 469": {
        "name": "Special Topics in Computer Graphics",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 471": {
        "name": "Networking II",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 473": {
        "name": "Software Testing, Reliability and Security",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 474": {
        "name": "Web Systems Architecture",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 475": {
        "name": "Requirements Engineering",
        "points": 3,
        "available_seats": 1
    },
    "CMPT 476": {
        "name": "Introduction to Quantum Algorithms",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 477": {
        "name": "Introduction to Formal Verification",
        "points": 2,
        "available_seats": 1
    },
    "CMPT 478": {
        "name": "Current Topics in Quantum Computing",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 479": {
        "name": "Special Topics in Computing Systems",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 489": {
        "name": "Special Topics in Programming Languages",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 493": {
        "name": "Digital Media Practicum",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 494": {
        "name": "Software Systems Program Capstone Project I",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 495": {
        "name": "Software Systems Capstone Project II",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 496": {
        "name": "Directed Studies",
        "points": 0,
        "available_seats": 1
    },
    "CMPT 497": {
        "name": "Dual Degree Program Capstone Project",
        "points": 0,
        "available_seats": 1
    },
    "CMPT 498": {
        "name": "Honours Research Project",
        "points": 1,
        "available_seats": 1
    },
    "CMPT 499": {
        "name": "Special Topics in Computer Hardware",
        "points": 1,
        "available_seats": 1
    }
}



