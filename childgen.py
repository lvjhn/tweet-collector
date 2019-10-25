import pandas as pd 
from string import punctuation
import re

puncs = list(punctuation) 
puncs.append("“")
puncs.append("”")


stopwords = """ 
i
me
my
myself
we
our
ours
ourselves
you
your
yours
yourself
yourselves
he
him
his
himself
she
her
hers
herself
it
its
itself
they
them
their
theirs
themselves
what
which
who
whom
this
that
these
those
am
is
are
was
were
be
been
being
have
has
had
having
do
does
did
doing
a
an
the
and
but
if
or
because
as
until
while
of
at
by
for
with
about
against
between
into
through
during
before
after
above
below
to
from
up
down
in
out
on
off
over
under
again
further
then
once
here
there
when
where
why
how
all
any
both
each
few
more
most
other
some
such
no
nor
not
only
own
same
so
than
too
very
s
t
can
will
just
don
should
now
@codysoyland
akin
aking
ako
alin
am
amin
aming
ang
ano
anumang
apat
at
atin
ating
ay
bababa
bago
bakit
bawat
bilang
dahil
dalawa
dapat
din
dito
doon
gagawin
gayunman
ginagawa
ginawa
ginawang
gumawa
gusto
habang
hanggang
hindi
huwag
iba
ibaba
ibabaw
ibig
ikaw
ilagay
ilalim
ilan
inyong
isa
isang
itaas
ito
iyo
iyon
iyong
ka
kahit
kailangan
kailanman
kami
kanila
kanilang
kanino
kanya
kanyang
kapag
kapwa
karamihan
katiyakan
katulad
kaya
kaysa
ko
kong
kulang
kumuha
kung
laban
lahat
lamang
likod
lima
maaari
maaaring
maging
mahusay
makita
marami
marapat
masyado
may
mayroon
mga
minsan
mismo
mula
muli
na
nabanggit
naging
nagkaroon
nais
nakita
namin
napaka
narito
nasaan
ng
ngayon
ni
nila
nilang
nito
niya
niyang
noon
o
pa
paano
pababa
paggawa
pagitan
pagkakaroon
pagkatapos
palabas
pamamagitan
panahon
pangalawa
para
paraan
pareho
pataas
pero
pumunta
pumupunta
sa
saan
sabi
sabihin
sarili
sila
sino
siya
tatlo
tayo
tulad
tungkol
una
walang
""".split("\n")

data = pd.read_csv("datasets/deep_filtered.csv") 

search_terms = ["african", "swine", "fever", "ejeep", "manok", "pula", "barreto",
                "sisters", "duterte", "robredo", "marcos", "sembreak", "kpop", 
                "alyas", "linda", "panelo", "tatay", "alex", "kadenang", "ginto",
                "cynthia", "villar"]

wordlist = {
    'English' : {}, 
    'Tagalog' : {}
}

# identify wordlist from both languages
for index, row in data.iterrows(): 
    text = row["text"]
    text = text.strip() 
    text = re.sub("\n", " ", text)
    text = re.sub("@[^\s]+", "", text)
    text = re.sub(r"http\S+", "", text)
    text = text.lower()

    # separate symbols from words 
    for punc in puncs: 
        text = text.replace(punc, " " + punc + " ")
    text = text.lower()
    words = text.split(" ") 

    # language 
    lang = row["language"]

    for word in words: 
        if word not in wordlist[lang] and word not in puncs and not word in stopwords and word not in search_terms: 
            wordlist[lang][word] = 1 
        elif word not in puncs and not word in stopwords and word not in search_terms: 
            wordlist[lang][word] += 1 

# Count Number of Words per Language 
print("No of Words per Language")
print("-------------------------------------")
print("English: " + str(len(wordlist["English"])))
print("Tagalog: " + str(len(wordlist["Tagalog"])))

# Order Words in Each Language 
wordlist_ordered = {
    'English' : dict(sorted(wordlist["English"].items(), key=lambda x: x[1], reverse=True)),
    'Tagalog' : dict(sorted(wordlist["Tagalog"].items(), key=lambda x: x[1], reverse=True)) 
} 

# Get the Top 10 from Each Language
en_top_10 = list(wordlist_ordered["English"].keys())[0:100]
tl_top_10 = list(wordlist_ordered["Tagalog"].keys())[0:1000]

print(en_top_10)
print(tl_top_10)