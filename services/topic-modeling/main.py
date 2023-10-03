import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from gensim import corpora
from gensim.models import LdaModel

nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english')) 

def preprocess_message(message):
    word_tokens = word_tokenize(message) 
    filtered_message = [w for w in word_tokens if not w in stop_words] 
    return filtered_message

# Assuming that twitch_messages is a list of messages from Twitch chat
twitch_messages = ["Hello world, this is a test message", "How are you today?", 
                   "I love playing this game!", "This is a cool stream", 
                   "Can't wait for the next event", "The game is too hard", 
                   "Enjoying the game play"]

documents = [preprocess_message(message) for message in twitch_messages]

# Create a Gensim dictionary from the documents
dictionary = corpora.Dictionary(documents)

# Create a Gensim corpus from the dictionary and the documents
corpus = [dictionary.doc2bow(document) for document in documents]

# Train the LDA model
lda = LdaModel(corpus, num_topics=3, id2word=dictionary)

# Print the top 5 topics
topics = lda.print_topics(num_words=5)
for topic in topics:
    print(topic)
