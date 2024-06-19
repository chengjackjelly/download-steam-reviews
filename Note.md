https://partner.steamgames.com/doc/store/getreviews
getdetail
https://store.steampowered.com/api/appdetails?appids=1174180
getidlist
http://api.steampowered.com/ISteamApps/GetAppList/v0002/
not sure if this contain the one we need? 
script:
https://github.com/woctezuma/download-steam-reviews

Bartle’s player types

Undertand Latent Dirichlet Allocation

mixtures of topics that split out words with certain probabilities

Perplexity values with 95% confidence interval

training process of LDA:
suppose we have K topics to discover from a set of documents,
for each documents:
        random assign each word to one of K topic,
        for each topic:
                p(topic t| document d)=?
                for each word:
                        p(word w| topic t)=?
