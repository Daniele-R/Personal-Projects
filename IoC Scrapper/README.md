# You got that right, IOC threat hunting just dropped
Probably nothing new, but here is a project for those who might struggle due to old processes, lack of funding, or simply lack of knowledge (just like me lol)

## How to?
Read the documentation, really. Don't even consider asking any questions about how it freaking works; it is rather easy. Fuck, even the code is perfectly commented for those new to the gist.

## How to make it yours
Rather simple as well: download it and make it work. My API is in there and I absolutely do not care. It was made in less than 2 minutes on OTX, and I'm pretty sure I could make another one hassle-free. I'm leaving the API there for those too lazy to want to make one. If it doesn't work, I am NOT making another. It is free, though.

## How to improve it?
Well, my first suggestion would be to simply have another source called something different, like "this is the app.exe," and just have a call to the ui.py. I am too lazy to do it. I could possibly ask Claude, GPT, or any other AI to do it for me, but I refuse.

## It grabs OTX, now what?
Great question! Now you keep adding other API sources that offer IOC ingestion. CISA offers one if your company pays and/or is related to the government. CrowdStrike offers one as well, in case you need it. I don't know, figure it out.

## What would be v2?
V2 would ideally be the project I was thinking of taking on, but my wings were split, cut, and then burned to the ground. Allegedly, I was flying too high. Hopefully that's not the case for you, dear reader. V2 would be a web scraper for those blogs you like, where CVEs are posted... Ideally, this is done with REGEX, as most of these blogs add the IOCs somewhere in fixed parts of their sites, but in case that is not the case, simply implement AI into the script to crawl and grab what you intend. The skeleton is already built; it's up to you, my dear, to keep working on it.

## Is this realistic?
Absolutely, although it wouldn't live as an executable, but as cloud code that will execute daily or so, with fixed parameters, so the IOCs are ingested hands-free. Remember, though: always do a human revision to validate that the IOCs ingested are not BS and/or disruptive to your company/agency.
