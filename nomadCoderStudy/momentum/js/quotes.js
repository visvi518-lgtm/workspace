const quotes = [
    {quote: "When you have faults, do not fear to abandon them.",
    author: "Confucius"
    },
    {quote: "They must often change who would be constant in happiness or wisdom.",
    author: "Confucius"
    },
    {quote: " Age is no guarantee of maturity. ",
    author: "Lawana Blackwell"
    },
    {quote: "Youth isn’t always all it’s touted to be. ",
    author: "Lawana Blackwell"
    },
    {quote: "You will face many defeats in life, but never let yourself be defeated.",
    author: "Maya Angelou"
    },
    {quote: "The greatest glory in living lies not in never falling, but in rising every time we fall.",
    author: "Nelson Mandela"
    },
    {quote: "ife is either a daring adventure or nothing at all.",
    author: "Helen Keller"
    },
    {quote: "The goal of life is living in agreement with nature.",
    author: "Zeno"
    },
    {quote: "This too shall pass.",
    author: "Et hoc transibit"
    },
    {quote: "Only I can change me life, no one can do it for me.",
    author: "Carol Burnett"
    }
]

const quote = document.querySelector("#quote span:first-child");
const author = document.querySelector("#quote span:last-child");

const randomNumber = Math.floor(Math.random()*quotes.length);
const todaysQuotes = quotes[randomNumber];

quote.innerText = todaysQuotes.quote;
author.innerText = todaysQuotes.author;



function randomNumberQuotesLog(){
    console.log(`랜덤상수 : `, randomNumber);
    console.log(`랜덤상수 `,randomNumber,`번째의 명언: `, quotes[randomNumber])
}



randomNumberQuotesLog();