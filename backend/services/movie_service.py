import json
import logging
import urllib.parse
from config import Config

logger = logging.getLogger(__name__)

# Try importing requests; fallback to urllib if not installed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.error
    import urllib.request


TMDB_GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}

# Mood to TMDB genre IDs
MOOD_GENRE_IDS = {
    "happy": [35, 16, 10751, 10402],    # Comedy, Animation, Family, Music
    "sad": [18, 10749, 16],             # Drama, Romance, Animation
    "angry": [28, 53, 80],              # Action, Thriller, Crime
    "fear": [27, 53, 9648],             # Horror, Thriller, Mystery
    "surprise": [878, 9648, 14],        # Sci-Fi, Mystery, Fantasy
    "neutral": [12, 35, 18],            # Adventure, Comedy, Drama
    "disgust": [35, 10751, 99],         # Comedy, Family, Documentary
}

# Curated fallback catalogue with real TMDB IDs, high-res posters, and synopses
CURATED_TMDB_MOVIES = {
    "happy": [
        {
            "id": 120467,
            "title": "The Grand Budapest Hotel",
            "genre": "Comedy, Drama",
            "year": "2014",
            "vote_average": 8.0,
            "poster_path": "/eWBy6g2J3r7d2r5a7oY99yQ7w9s.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/eWBy6g2J3r7d2r5a7oY99yQ7w9s.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/lY2DhbA77spI27kbe18f4t9DqP3.jpg",
            "overview": "The adventures of Gustave H, a legendary concierge at a famous European hotel, and Zero Moustafa, the lobby boy who becomes his most trusted friend.",
            "tmdb_url": "https://www.themoviedb.org/movie/120467",
        },
        {
            "id": 313369,
            "title": "La La Land",
            "genre": "Comedy, Drama, Music",
            "year": "2016",
            "vote_average": 7.9,
            "poster_path": "/uDO8zWDhfWwoFdKS4fzkVJb0Rf0.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkVJb0Rf0.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/qJeU7KM4nR29vM8z59N1mC4Q2Tf.jpg",
            "overview": "Mia, an aspiring actress, and Sebastian, a dedicated jazz musician, struggle to make ends meet in a city known for crushing hopes and breaking hearts.",
            "tmdb_url": "https://www.themoviedb.org/movie/313369",
        },
        {
            "id": 346648,
            "title": "Paddington 2",
            "genre": "Family, Comedy, Adventure",
            "year": "2017",
            "vote_average": 7.6,
            "poster_path": "/a4BfxRK8RJgb52wPOGJ0tl9cuZy.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/a4BfxRK8RJgb52wPOGJ0tl9cuZy.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/vVp1MRnJ4GgG9FhE1oY46kP3TzG.jpg",
            "overview": "Paddington settles into life with the Brown family, taking on odd jobs to buy a unique pop-up book for his Aunt Lucy's 100th birthday.",
            "tmdb_url": "https://www.themoviedb.org/movie/346648",
        },
        {
            "id": 324857,
            "title": "Spider-Man: Into the Spider-Verse",
            "genre": "Animation, Action, Adventure",
            "year": "2018",
            "vote_average": 8.4,
            "poster_path": "/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/7d6ZJe091kduvOHQm12VIcZq164.jpg",
            "overview": "Teen Miles Morales becomes the new Spider-Man and joins other Spider-Heroes from alternate dimensions to stop a threat to all reality.",
            "tmdb_url": "https://www.themoviedb.org/movie/324857",
        },
        {
            "id": 438695,
            "title": "Sing 2",
            "genre": "Animation, Comedy, Family",
            "year": "2021",
            "vote_average": 7.9,
            "poster_path": "/aWeKITRFbbwY8txG5uCj4rMCfSP.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/aWeKITRFbbwY8txG5uCj4rMCfSP.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/tq3dvLMgs09Z874a17Fq5F4gZzR.jpg",
            "overview": "Buster Moon and his musically talented friends must persuade reclusive rock star Clay Calloway to join them for the opening of a smash stage show.",
            "tmdb_url": "https://www.themoviedb.org/movie/438695",
        },
    ],
    "sad": [
        {
            "id": 150540,
            "title": "Inside Out",
            "genre": "Animation, Family, Drama",
            "year": "2015",
            "vote_average": 7.9,
            "poster_path": "/2H1TmgdfNbfKlUkIZgfd41wImgq.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/2H1TmgdfNbfKlUkIZgfd41wImgq.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/jOzrPnWiqBh8n2Bg9FyIjHGQzoc.jpg",
            "overview": "Growing up can be a bumpy road, and it's no exception for Riley, whose emotions—Joy, Fear, Anger, Disgust, and Sadness—guide her through life.",
            "tmdb_url": "https://www.themoviedb.org/movie/150540",
        },
        {
            "id": 1402,
            "title": "The Pursuit of Happyness",
            "genre": "Drama",
            "year": "2006",
            "vote_average": 8.0,
            "poster_path": "/fGsc4Bjhx69nFjTqFm1z4v8y1qN.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/fGsc4Bjhx69nFjTqFm1z4v8y1qN.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/vL5W26zihc681E7p1MvF1tB457v.jpg",
            "overview": "A struggling salesman takes custody of his young son as he's poised to begin a life-changing professional endeavor in stockbroking.",
            "tmdb_url": "https://www.themoviedb.org/movie/1402",
        },
        {
            "id": 489,
            "title": "Good Will Hunting",
            "genre": "Drama",
            "year": "1997",
            "vote_average": 8.2,
            "poster_path": "/bABCBKYBK7A7GZ0t40T0382B21.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/bABCBKYBK7A7GZ0t40T0382B21.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/jcTq6R2G7p4Y7E5s4K9o3w5T7u.jpg",
            "overview": "Will Hunting, a janitor at MIT, has a gift for mathematics, but needs help from a psychologist to find direction in his life.",
            "tmdb_url": "https://www.themoviedb.org/movie/489",
        },
        {
            "id": 207,
            "title": "Dead Poets Society",
            "genre": "Drama",
            "year": "1989",
            "vote_average": 8.3,
            "poster_path": "/ai409Y4Soxw72jKxR3K2mN6P7lP.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/ai409Y4Soxw72jKxR3K2mN6P7lP.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/avZ8p81kZt6z7Fh9g7o5P4m3k.jpg",
            "overview": "English teacher John Keating inspires his students to look at poetry and life from a different perspective at an authentic boarding school.",
            "tmdb_url": "https://www.themoviedb.org/movie/207",
        },
        {
            "id": 508442,
            "title": "Soul",
            "genre": "Animation, Comedy, Drama",
            "year": "2020",
            "vote_average": 8.1,
            "poster_path": "/hm58o4DuWz2r8i7k2t4t0q8pY8.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/hm58o4DuWz2r8i7k2t4t0q8pY8.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/kf456Z9Z7X6m5P3lK8o7Y9wR1.jpg",
            "overview": "After landing the gig of a lifetime, a New York jazz pianist suddenly finds himself trapped in a strange land between Earth and the afterlife.",
            "tmdb_url": "https://www.themoviedb.org/movie/508442",
        },
    ],
    "angry": [
        {
            "id": 278,
            "title": "The Shawshank Redemption",
            "genre": "Drama, Crime",
            "year": "1994",
            "vote_average": 8.7,
            "poster_path": "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/kXfqAk2MHANLwNuLkncu0Rdyq7.jpg",
            "overview": "Imprisoned in the 1940s for a double murder he didn't commit, Andy Dufresne forms an enduring bond with fellow inmate Red while maintaining resilience.",
            "tmdb_url": "https://www.themoviedb.org/movie/278",
        },
        {
            "id": 244786,
            "title": "Whiplash",
            "genre": "Drama, Music",
            "year": "2014",
            "vote_average": 8.4,
            "poster_path": "/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/6bbZ6XyvgfjhQwfplVUhBu2fhwd.jpg",
            "overview": "Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at all costs.",
            "tmdb_url": "https://www.themoviedb.org/movie/244786",
        },
        {
            "id": 1366,
            "title": "Rocky",
            "genre": "Drama, Sports",
            "year": "1976",
            "vote_average": 7.8,
            "poster_path": "/i5XPd9tt9J1pSV0Y5E0r4Xw3U5t.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/i5XPd9tt9J1pSV0Y5E0r4Xw3U5t.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/2k9WjRpNf197L84m44qK5j5T3.jpg",
            "overview": "A small-time Philadelphia boxer gets a supremely rare chance to fight the world heavyweight champion Apollo Creed in a bout in which he strives to go the distance.",
            "tmdb_url": "https://www.themoviedb.org/movie/1366",
        },
        {
            "id": 76341,
            "title": "Mad Max: Fury Road",
            "genre": "Action, Adventure, Sci-Fi",
            "year": "2015",
            "vote_average": 7.6,
            "poster_path": "/hA2ple9q4qnwxp3hKVNhroipsir.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/hA2ple9q4qnwxp3hKVNhroipsir.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/nlCHUWjY9XWbuEUQauCBgnY8ymF.jpg",
            "overview": "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of a group of female prisoners and a drifter named Max.",
            "tmdb_url": "https://www.themoviedb.org/movie/76341",
        },
        {
            "id": 98,
            "title": "Gladiator",
            "genre": "Action, Drama, Adventure",
            "year": "2000",
            "vote_average": 8.2,
            "poster_path": "/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/k7e1nC5a2j8d9F7g5H3k2P1wR4.jpg",
            "overview": "In the year 180, the death of emperor Marcus Aurelius throws the Roman Empire into turmoil. Maximus Decimus Meridius is betrayed and forced into slavery as a gladiator.",
            "tmdb_url": "https://www.themoviedb.org/movie/98",
        },
    ],
    "fear": [
        {
            "id": 447332,
            "title": "A Quiet Place",
            "genre": "Horror, Drama, Sci-Fi",
            "year": "2018",
            "vote_average": 7.4,
            "poster_path": "/nAU74GmpUk7t5iklEp3bufwDq4n.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/nAU74GmpUk7t5iklEp3bufwDq4n.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/roYyPiQDytnk6ghwf9219hpIS15.jpg",
            "overview": "A family must navigate their lives in silence to avoid mysterious creatures that hunt exclusively by sound.",
            "tmdb_url": "https://www.themoviedb.org/movie/447332",
        },
        {
            "id": 419430,
            "title": "Get Out",
            "genre": "Mystery, Thriller, Horror",
            "year": "2017",
            "vote_average": 7.6,
            "poster_path": "/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/4B5Q7K6rT9g5H2k8o7Y9wR1X3.jpg",
            "overview": "Chris and his girlfriend Rose have reached the meet-the-parents milestone of dating, she invites him for a weekend getaway upstate with her family.",
            "tmdb_url": "https://www.themoviedb.org/movie/419430",
        },
        {
            "id": 138843,
            "title": "The Conjuring",
            "genre": "Horror, Thriller",
            "year": "2013",
            "vote_average": 7.5,
            "poster_path": "/wVYREutTvI2tmxr6ujrHT704wGF.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/wVYREutTvI2tmxr6ujrHT704wGF.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/5BwqwxqnQl43G2nZpQeR1T3y.jpg",
            "overview": "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized by a dark presence in their secluded farmhouse.",
            "tmdb_url": "https://www.themoviedb.org/movie/138843",
        },
        {
            "id": 11324,
            "title": "Shutter Island",
            "genre": "Drama, Mystery, Thriller",
            "year": "2010",
            "vote_average": 8.2,
            "poster_path": "/4GDy0PHYX3VRXUtwK5ysFbg3kEx.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/4GDy0PHYX3VRXUtwK5ysFbg3kEx.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/c54HpT2Aea4q0v8D9f5G3k1P2.jpg",
            "overview": "In 1954, a U.S. Marshal investigates the disappearance of a murderer who escaped from a hospital for the criminally insane.",
            "tmdb_url": "https://www.themoviedb.org/movie/11324",
        },
        {
            "id": 274,
            "title": "The Silence of the Lambs",
            "genre": "Crime, Drama, Thriller",
            "year": "1991",
            "vote_average": 8.3,
            "poster_path": "/uS9m8OBk1A8eM9I042bx8XXUNAq.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXUNAq.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/mfwq2nMBzArGQay6EbZzR46r0wS.jpg",
            "overview": "Clarice Starling, an ambitious FBI trainee, ventures into an eerie maximum-security asylum to interrogate psychiatrist and cannibal Dr. Hannibal Lecter.",
            "tmdb_url": "https://www.themoviedb.org/movie/274",
        },
    ],
    "surprise": [
        {
            "id": 27205,
            "title": "Inception",
            "genre": "Action, Sci-Fi, Adventure",
            "year": "2010",
            "vote_average": 8.4,
            "poster_path": "/oYuLEt3zVCKq57qu25afm89xQ88.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu25afm89xQ88.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/s3TBrRGB1iav7gFOCNx3H31MoES.jpg",
            "overview": "Cobb, a skilled thief who steals corporate secrets through dream-sharing technology, is given the inverse task of planting an idea into the mind of a CEO.",
            "tmdb_url": "https://www.themoviedb.org/movie/27205",
        },
        {
            "id": 496243,
            "title": "Parasite",
            "genre": "Comedy, Thriller, Drama",
            "year": "2019",
            "vote_average": 8.5,
            "poster_path": "/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/hiKmpRAueTkFrSDmZArr0T05Q77.jpg",
            "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
            "tmdb_url": "https://www.themoviedb.org/movie/496243",
        },
        {
            "id": 157336,
            "title": "Interstellar",
            "genre": "Adventure, Drama, Sci-Fi",
            "year": "2014",
            "vote_average": 8.4,
            "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
            "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.",
            "tmdb_url": "https://www.themoviedb.org/movie/157336",
        },
        {
            "id": 1124,
            "title": "The Prestige",
            "genre": "Drama, Mystery, Sci-Fi",
            "year": "2006",
            "vote_average": 8.2,
            "poster_path": "/bdN3gEYYz49VR902BH85D7eE89n.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/bdN3gEYYz49VR902BH85D7eE89n.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/5Ue53iV8hT8z6K9o4w7T1P2X3.jpg",
            "overview": "A mysterious story of two magicians whose intense rivalry leads them on a life-long battle for supremacy full of obsession, deceit, and jealousy.",
            "tmdb_url": "https://www.themoviedb.org/movie/1124",
        },
        {
            "id": 546554,
            "title": "Knives Out",
            "genre": "Comedy, Mystery, Crime",
            "year": "2019",
            "vote_average": 7.9,
            "poster_path": "/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/Ab8mkHmkYADjU7wQiOkia9BzGvS.jpg",
            "overview": "When renowned crime novelist Harlan Thrombey is found dead at his estate, the inquisitive detective Benoit Blanc is mysteriously enlisted to investigate.",
            "tmdb_url": "https://www.themoviedb.org/movie/546554",
        },
    ],
    "neutral": [
        {
            "id": 37165,
            "title": "The Truman Show",
            "genre": "Comedy, Drama",
            "year": "1998",
            "vote_average": 8.1,
            "poster_path": "/vuza0WqY239muDc1HNw0dnZXvVv.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/vuza0WqY239muDc1HNw0dnZXvVv.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/5P4m3k2P1wR4T6y8m47V4oZ9.jpg",
            "overview": "An insurance salesman discovers his whole life is actually a reality TV show broadcast live to the entire world 24/7.",
            "tmdb_url": "https://www.themoviedb.org/movie/37165",
        },
        {
            "id": 116745,
            "title": "The Secret Life of Walter Mitty",
            "genre": "Adventure, Comedy, Drama",
            "year": "2013",
            "vote_average": 7.2,
            "poster_path": "/eL5e4hD7jC2R1v7p1X9o5P3k4.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/eL5e4hD7jC2R1v7p1X9o5P3k4.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/6rQ0oZ874a17Fq5F4gZzR9wR1.jpg",
            "overview": "A timid magazine photo manager who lives life vicariously through daydreams embarks on a true-life global journey when a negative goes missing.",
            "tmdb_url": "https://www.themoviedb.org/movie/116745",
        },
        {
            "id": 212778,
            "title": "Chef",
            "genre": "Comedy, Drama",
            "year": "2014",
            "vote_average": 7.5,
            "poster_path": "/z37H0Z2h1k4P3lK8o7Y9wR1X3.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/z37H0Z2h1k4P3lK8o7Y9wR1X3.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/5B456Z9Z7X6m5P3lK8o7Y9wR1.jpg",
            "overview": "A head chef quits his prominent restaurant job and buys a food truck in an effort to reclaim his creative promise and reconnect with his family.",
            "tmdb_url": "https://www.themoviedb.org/movie/212778",
        },
        {
            "id": 122906,
            "title": "About Time",
            "genre": "Drama, Romance, Fantasy",
            "year": "2013",
            "vote_average": 7.9,
            "poster_path": "/i8ogQ5qg1eB9U2p0d6oE5j8rT9.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/i8ogQ5qg1eB9U2p0d6oE5j8rT9.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/4rT9g5H2k8o7Y9wR1X3P5s3G2.jpg",
            "overview": "At the age of 21, Tim discovers he can travel in time and change what happens and has happened in his own life, focusing his efforts on making love work.",
            "tmdb_url": "https://www.themoviedb.org/movie/122906",
        },
        {
            "id": 10315,
            "title": "Fantastic Mr. Fox",
            "genre": "Animation, Comedy, Adventure",
            "year": "2009",
            "vote_average": 7.8,
            "poster_path": "/njHNErIK70jGda5f58da9Lwt08o.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/njHNErIK70jGda5f58da9Lwt08o.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/6a17t9rXbT6mZ9Z1P3lC7k9wR2.jpg",
            "overview": "An urbane fox cannot resist returning to his farm-raiding ways and then must help his community survive the farmers' retaliation.",
            "tmdb_url": "https://www.themoviedb.org/movie/10315",
        },
    ],
    "disgust": [
        {
            "id": 2062,
            "title": "Ratatouille",
            "genre": "Animation, Comedy, Family",
            "year": "2007",
            "vote_average": 7.8,
            "poster_path": "/npHNErIK70jGda5f58da9Lwt08o.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/npHNErIK70jGda5f58da9Lwt08o.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/ex4tL2N94zK78f0m9P3lC7k9wR2.jpg",
            "overview": "Remy, a resident of Paris, dreams of becoming a great French chef despite the obvious problem of being a rat in a definitely rodent-phobic profession.",
            "tmdb_url": "https://www.themoviedb.org/movie/2062",
        },
        {
            "id": 10681,
            "title": "WALL·E",
            "genre": "Animation, Family, Sci-Fi",
            "year": "2008",
            "vote_average": 8.1,
            "poster_path": "/hbhFnRzzg6ZDmm8YAmxBnQpQIPh.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/hbhFnRzzg6ZDmm8YAmxBnQpQIPh.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/fK5ssFh00q0992dVxR4mC707.jpg",
            "overview": "In a distant, desolate future, a small waste-collecting robot inadvertently embarks on a space journey that will ultimately decide the fate of mankind.",
            "tmdb_url": "https://www.themoviedb.org/movie/10681",
        },
        {
            "id": 24226,
            "title": "Julie & Julia",
            "genre": "Comedy, Drama, Biography",
            "year": "2009",
            "vote_average": 6.8,
            "poster_path": "/x9v7p6rY8e4w9s2k5e0p1r6t8u.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/x9v7p6rY8e4w9s2k5e0p1r6t8u.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/vVp1MRnJ4GgG9FhE1oY46kP3TzG.jpg",
            "overview": "Julia Child's story of her start in the cooking profession is intertwined with 2002 blogger Julie Powell's challenge to cook all the recipes in Child's first book.",
            "tmdb_url": "https://www.themoviedb.org/movie/24226",
        },
        {
            "id": 82691,
            "title": "Jiro Dreams of Sushi",
            "genre": "Documentary",
            "year": "2011",
            "vote_average": 7.8,
            "poster_path": "/k8p6o5u3y1r4t6w9e2p0o8i7u.jpg",
            "poster_url": "https://image.tmdb.org/t/p/w500/k8p6o5u3y1r4t6w9e2p0o8i7u.jpg",
            "backdrop_url": "https://image.tmdb.org/t/p/w780/tq3dvLMgs09Z874a17Fq5F4gZzR.jpg",
            "overview": "A documentary on 85-year-old sushi master Jiro Ono, his renowned Tokyo restaurant, and his relationship with his son and eventual heir, Yoshikazu.",
            "tmdb_url": "https://www.themoviedb.org/movie/82691",
        },
    ],
}


class MovieService:
    def recommend(self, mood: str) -> dict:
        mood_lower = mood.lower() if mood else "neutral"
        if mood_lower not in MOOD_GENRE_IDS:
            mood_lower = "neutral"

        mood_messages = {
            "happy": "Uplifting, high-spirited, and vibrant films to match your joyful energy!",
            "sad": "Comforting, cathartic, and soul-stirring films offering gentle emotional resonance.",
            "angry": "Empowering, intense, and adrenaline-charged cinema to channel your passion.",
            "fear": "Spine-chilling thrillers and edge-of-your-seat psychological suspense.",
            "surprise": "Mind-bending twists, high-concept wonder, and unexpected narratives.",
            "neutral": "Aesthetic, engaging, and beautifully balanced cinematic masterpieces.",
            "disgust": "Delightful, heartwarming palate cleansers and culinary adventures to refresh your mood.",
        }

        # Attempt dynamic live fetch from TMDB if API key is provided
        tmdb_api_key = Config.TMDB_API_KEY.strip() if Config.TMDB_API_KEY else ""
        if tmdb_api_key:
            live_movies = self._fetch_from_tmdb(mood_lower, tmdb_api_key)
            if live_movies:
                return {
                    "mood": mood_lower,
                    "message": mood_messages.get(mood_lower, mood_messages["neutral"]),
                    "movies": live_movies,
                    "source": "tmdb_live",
                }

        # Use rich curated TMDB catalogue with authentic poster URLs and metadata
        curated_movies = CURATED_TMDB_MOVIES.get(mood_lower, CURATED_TMDB_MOVIES["neutral"])
        return {
            "mood": mood_lower,
            "message": mood_messages.get(mood_lower, mood_messages["neutral"]),
            "movies": curated_movies,
            "source": "tmdb_curated",
        }

    def _fetch_from_tmdb(self, mood: str, api_key: str) -> list[dict] | None:
        genre_ids = MOOD_GENRE_IDS.get(mood, [35, 18])
        genre_param = "|".join(str(g) for g in genre_ids)

        params = {
            "api_key": api_key,
            "with_genres": genre_param,
            "sort_by": "popularity.desc",
            "vote_count.gte": 150,
            "vote_average.gte": 6.8,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        }

        url = f"{Config.TMDB_BASE_URL.rstrip('/')}/discover/movie?{urllib.parse.urlencode(params)}"

        try:
            data = None
            if REQUESTS_AVAILABLE:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "WellSync/1.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))

            if not data or "results" not in data:
                return None

            results = []
            for item in data["results"][:12]:
                poster_path = item.get("poster_path")
                backdrop_path = item.get("backdrop_path")
                # Format genres
                genres = [TMDB_GENRE_MAP.get(gid, "Drama") for gid in item.get("genre_ids", [])[:3]]
                genre_str = ", ".join(genres) if genres else "Cinema"

                results.append({
                    "id": item.get("id"),
                    "title": item.get("title", "Untitled"),
                    "genre": genre_str,
                    "year": (item.get("release_date") or "")[:4],
                    "vote_average": round(item.get("vote_average", 0), 1),
                    "poster_path": poster_path,
                    "poster_url": f"{Config.TMDB_IMAGE_BASE_URL.rstrip('/')}{poster_path}" if poster_path else None,
                    "backdrop_url": f"{Config.TMDB_BACKDROP_BASE_URL.rstrip('/')}{backdrop_path}" if backdrop_path else None,
                    "overview": item.get("overview", "No synopsis available."),
                    "tmdb_url": f"https://www.themoviedb.org/movie/{item.get('id')}",
                })

            return results if results else None
        except Exception as e:
            logger.warning(f"Failed to fetch live recommendations from TMDB: {e}")
            return None


movie_service = MovieService()
