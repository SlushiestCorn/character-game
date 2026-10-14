"""Build an inspectable, offline character catalogue.

Rows: Name | exact English Wikipedia title (or - for inferred) | semicolon-separated traits.
Group-level tags identify formats/themes; per-character tags capture diverse factual traits.
Avoid inserting an unverified trait: games rely on these being true for BOTH characters.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

# Curated, human-readable labels are the ONLY tags that can become a displayed link.
LINKS = {
 'green':'Both characters are predominantly green.',
 'blue':'Both characters are associated with the colour blue.',
 'red':'Both characters are associated with the colour red.',
 'purple':'Both characters are associated with the colour purple.',
 'yellow':'Both characters are associated with the colour yellow.',
 'glasses':'Both characters wear glasses.',
 'hat':'Both characters regularly wear a distinctive hat or head covering.',
 'mask':'Both characters wear a mask or disguise.',
 'cape':'Both characters are known for wearing a cape or cloak.',
 'facial-hair':'Both characters are known for facial hair.',
 'bald':'Both characters are recognisably bald.',
 'long-hair':'Both characters are known for long hair.',
 'scar':'Both characters have a notable scar or visible mark.',
 'small':'Both characters are notably small.',
 'giant':'Both characters are unusually large or gigantic.',
 'animal':'Both characters are animals or animal-like beings.',
 'talking-animal':'Both characters are animals that can talk.',
 'robot':'Both characters are robots or artificial intelligences.',
 'alien':'Both characters come from another planet.',
 'nonhuman':'Neither character is an ordinary human.',
 'monster':'Both characters are monsters or monstrous beings.',
 'ghost':'Both characters have been portrayed as ghosts or spirits.',
 'undead':'Both characters are undead.',
 'royalty':'Both characters belong to royalty.',
 'leader':'Both characters have led a group or organisation.',
 'villain':'Both characters have been major antagonists.',
 'hero':'Both characters have acted as heroes.',
 'antihero':'Both characters have acted as antiheroes.',
 'sidekick':'Both characters are recognised companions or sidekicks.',
 'detective':'Both characters have worked as detectives or investigators.',
 'scientist':'Both characters work in science or research.',
 'inventor':'Both characters invent things.',
 'doctor':'Both characters have been medical doctors.',
 'teacher':'Both characters have been teachers or mentors.',
 'student':'Both characters have been students.',
 'chef':'Both characters work with food or cooking.',
 'musician':'Both characters perform music.',
 'singer':'Both characters sing professionally or as a defining role.',
 'actor':'Both characters work as performers or actors.',
 'athlete':'Both characters are athletes or sportspeople.',
 'writer':'Both characters write books or literature.',
 'artist':'Both characters make visual art.',
 'politician':'Both characters have held political office or leadership.',
 'military':'Both characters have served as soldiers or military commanders.',
 'criminal':'Both characters have committed crimes.',
 'pirate':'Both characters are pirates.',
 'spy':'Both characters have worked as spies or secret agents.',
 'explorer':'Both characters are explorers or adventurers.',
 'magic':'Both characters can use magic or supernatural powers.',
 'super-strength':'Both characters possess exceptional physical strength.',
 'flight':'Both characters can fly without a conventional aircraft.',
 'telepathy':'Both characters have used telepathy or mind powers.',
 'shapeshift':'Both characters have transformed into other forms.',
 'time-travel':'Both characters have travelled through time.',
 'immortal':'Both characters have unusually long lives or immortality.',
 'sword':'Both characters are associated with swords or bladed weapons.',
 'bow':'Both characters have used bows and arrows.',
 'gun':'Both characters are known for using firearms.',
 'martial-arts':'Both characters are trained in hand-to-hand combat.',
 'weapon':'Both characters are known for using weapons.',
 'fire':'Both characters have powers or stories involving fire.',
 'water':'Both characters have powers or stories involving water.',
 'ice':'Both characters have powers or stories involving ice.',
 'lightning':'Both characters have powers or stories involving lightning.',
 'space':'Both characters have travelled into space.',
 'underwater':'Both characters have spent significant time underwater.',
 'forest':'Both characters are closely associated with forests or nature.',
 'desert':'Both characters are associated with deserts.',
 'island':'Both characters are associated with islands.',
 'castle':'Both characters have lived or worked in a castle.',
 'school':'Both characters are associated with a school or academy.',
 'laboratory':'Both characters are associated with laboratories.',
 'family':'Family relationships play a major role in both characters’ stories.',
 'parent':'Both characters are parents.',
 'orphan':'Both characters lost their parents or were orphaned.',
 'sibling':'Both characters have a notable sibling relationship.',
 'twins':'Both characters are twins.',
 'pet':'Both characters have an animal companion or pet.',
 'secret-identity':'Both characters use an important secret or alternate identity.',
 'double-life':'Both characters have led a notable double life.',
 'transformation':'Both characters undergo a major physical transformation.',
 'redemption':'Both characters have a prominent redemption arc.',
 'betrayal':'Both characters have experienced or committed a major betrayal.',
 'revenge':'Both characters have sought revenge.',
 'resurrection':'Both characters have returned from death.',
 'chosen-one':'Both characters have been treated as chosen or destined figures.',
 'prophecy':'Prophecy plays a major role in both characters’ stories.',
 'wealthy':'Both characters are notably wealthy.',
 'poor':'Both characters have experienced significant poverty.',
 'royal-adviser':'Both characters have advised rulers.',
 'court':'Both characters have appeared in court or legal proceedings.',
 'prison':'Both characters have been imprisoned.',
 'travel':'Both characters travel extensively.',
 'technology':'Both characters rely heavily on advanced technology.',
 'vehicle':'Both characters use a distinctive vehicle.',
 'musical-instrument':'Both characters play a musical instrument.',
 'competition':'Both characters participate in contests or competitions.',
 'team':'Both characters are associated with a well-known team.',
 'friendship':'Friendship is a central part of both characters’ stories.',
 'rival':'Both characters have a significant rivalry.',
 'romance':'Romance is significant in both characters’ stories.',
 'comedy':'Both characters are strongly associated with comedy.',
 'horror':'Both characters are strongly associated with horror.',
 'mystery':'Both characters are associated with mysteries or investigations.',
 'fantasy':'Both characters appear in fantasy settings or stories.',
 'sci-fi':'Both characters appear in science-fiction settings or stories.',
 'animation':'Both characters have appeared in animated productions.',
 'video-game':'Both characters have appeared in video games.',
 'novel':'Both characters appear in novels or literary works.',
 'comics':'Both characters appear in comic books or graphic novels.',
 'film':'Both characters have appeared in feature films.',
 'television':'Both characters have appeared on television.',
 'theatre':'Both characters have appeared in stage works.',
 'folklore':'Both characters originate in mythology, legend or folklore.',
 'real':'Both characters are real people.',
 'fictional':'Both characters are fictional.',
 'history':'Both characters have played a role in historical events.',
 'award':'Both characters have won a major award or honour.',
 'british':'Both characters are British.',
 'american':'Both characters are American.',
 'japanese':'Both characters are Japanese.',
 'french':'Both characters are French.',
 'australian':'Both characters are Australian.',
 'european':'Both characters come from Europe.',
 'asian':'Both characters come from Asia.',
 'african':'Both characters come from Africa.',
 'royal-family':'Both characters are part of a ruling family.',
 'historical-figure':'Both characters are historical figures.',
 'sports':'Both characters are associated with competitive sport.',
 'media':'Both characters are prominent in mass media.',
 'education':'Both characters have worked in education.',
 'activist':'Both characters have advocated for social or political change.',
 'entrepreneur':'Both characters have founded or led businesses.',
 'religion':'Both characters are associated with religious history or stories.',
 'adventure':'Both characters are involved in adventure stories.',
 'costume':'Both characters wear distinctive costumes.',
 'armor':'Both characters wear protective armour.',
 'dragon':'Both characters are associated with dragons.',
 'horse':'Both characters are associated with horses.',
 'dinosaur':'Both characters are associated with dinosaurs.',
 'vehicle-driver':'Both characters regularly drive or pilot vehicles.',
 'wizard':'Both characters are wizards, witches or magic users.',
 'mentor':'Both characters serve as mentors.',
 'apprentice':'Both characters have trained as apprentices.',
 'family-business':'Both characters have been involved in a family business.',
 'leadership-conflict':'Both characters have struggled over leadership or power.',
 'identity':'Questions of identity are important to both characters’ stories.',
 'technology-inventor':'Both characters have created notable technology.',
 'nature':'Both characters have a close bond with nature.',
 'lost-home':'Both characters have lost or left their home.',
 'search':'Both characters have undertaken an important search or quest.',
 'survival':'Both characters have survived dangerous circumstances.',
 'trickster':'Both characters are tricksters or practical jokers.',
 'married':'Both characters have been married.',
 'young':'Both characters are depicted as young or youthful.',
 'elder':'Both characters are depicted as elderly or long-lived.',
 'superhero':'Both characters are superheroes.',
 'combat':'Both characters are experienced fighters.',
 'royal-court':'Both characters have connections to a royal court.',
 'spacecraft':'Both characters have travelled in spacecraft.',
 'rebel':'Both characters have rebelled against an authority.',
 'law':'Both characters are associated with law enforcement or legal work.',
 'royal-heir':'Both characters have been heirs to a throne.',
 'animal-lover':'Both characters are notably fond of animals.',
 'supernatural':'Both characters are linked to supernatural phenomena.',
 'musical':'Both characters are associated with musical stories or performances.',
 'wartime':'Both characters have lived through or participated in war.',
 'detective-fiction':'Both characters appear in detective or mystery fiction.',
 'artificial':'Both characters were created or constructed rather than born conventionally.',
 'isolation':'Both characters have spent time in significant isolation.',
 'public-figure':'Both characters have been widely recognised public figures.',
}

# Some tags are meaningful metadata for filtering but do not make good round clues.
NEVER_LINK = {'real','fictional','male','female','human','film','television','media','american','european','asian','public-figure','history','historical-figure','comedy','fantasy','sci-fi','adventure','animation','video-game','novel','comics','actor','sports','young','team','family','travel','competition','award','wealthy','parent','friendship','romance','hero','villain','animal','nonhuman','musician','singer'}
# For broad links, use a higher minimum pool to avoid being too revealing.
MIN_POOL = 12

# Cohorts of characters from very different genres and levels of fame.
# Last field = group shared traits; records can freely extend or override through their own traits.
GROUPS=[]
def group(work, medium, shared, text):
    GROUPS.append((work,medium,shared,text))

group('Shrek','animated film','fictional animation film fantasy comedy adventure', '''
Shrek|Shrek|green nonhuman monster hero parent married romance friend friendship swamp isolation
Fiona|Princess Fiona|green royalty transformation magic combat romance parent castle secret-identity
Donkey|Donkey (Shrek)|animal talking-animal sidekick friendship comedy singer adventure
Puss in Boots|Puss in Boots (Shrek)|animal talking-animal sword hat boots combat hero adventure
Lord Farquaad|Lord Farquaad|villain leader royalty castle small wealthy court
Dragon|Dragon (Shrek)|dragon nonhuman flight fire giant romance animal
Gingy|Gingerbread Man (Shrek)|small nonhuman artificial survival comedy friendship
Fairy Godmother|Fairy Godmother (Shrek)|magic villain singer parent wealthy royal-court
King Harold|King Harold (Shrek)|royalty parent married secret-identity transformation castle
Prince Charming|Prince Charming (Shrek)|royalty villain sword romance revenge leadership-conflict
''')
group('Toy Story','animated film','fictional animation film comedy adventure friendship', '''
Woody|Sheriff Woody|hat leader hero toy artificial cowboy loyalty rival friendship
Buzz Lightyear|Buzz Lightyear|space costume technology flight toy artificial hero rival
Jessie|Jessie (Toy Story)|hat toy artificial hero singer adventure friendship
Bo Peep|Bo Peep (Toy Story)|toy artificial shepherd hero romance mentor
Rex|Rex (Toy Story)|dinosaur animal artificial toy comedy fear
Hamm|Hamm (Toy Story)|animal artificial toy comedy wealthy
Mr. Potato Head|Mr. Potato Head|artificial toy comedy transformation parent married
Slinky Dog|Slinky Dog|animal artificial toy friendship sidekick
Lotso|Lots-o'-Huggin' Bear|animal artificial toy villain leader betrayal prison
Forky|Forky|artificial toy small identity comedy friendship
''')
group('Frozen','animated film','fictional animation film fantasy musical royalty family', '''
Elsa|Elsa (Frozen)|royalty ice magic queen sibling leader castle isolation transformation
Anna|Anna (Frozen)|royalty sibling romance adventure hero castle friendship
Olaf|Olaf (Frozen)|artificial magic nonhuman snow comic relief friendship young
Kristoff|Kristoff (Frozen)|forest nature animal-lover horse romance adventure
Sven|Sven (Frozen)|animal deer friendship sidekick nature
Hans|Hans (Frozen)|royalty villain betrayal romance leadership-conflict sword
Oaken|Oaken (Frozen)|entrepreneur shopkeeper family-business comedy
Grand Pabbie|Grand Pabbie|nonhuman magic elder mentor forest
Marshmallow|Marshmallow (Frozen)|artificial ice monster nonhuman giant guardian
Duke of Weselton|Duke of Weselton|villain wealthy royal-court leader comedy
''')
group('The Lion King','animated film','fictional animation film animal talking-animal adventure family nature', '''
Simba|Simba|royalty leader hero orphan revenge parent married forest royal-heir
Nala|Nala (The Lion King)|royalty leader hero parent married nature combat
Mufasa|Mufasa|royalty leader parent married mentor betrayal elder
Scar|Scar (The Lion King)|villain royalty sibling betrayal leader scar revenge royal-heir
Timon|Timon and Pumbaa|sidekick comedy friendship trickster small
Pumbaa|Timon and Pumbaa|sidekick comedy friendship nature
Rafiki|Rafiki|mentor magic spiritual nature elder royal-adviser
Zazu|Zazu (The Lion King)|royal-adviser flight sidekick comedy leader
Shenzi|Shenzi, Banzai and Ed|villain team comedy forest
Sarabi|Sarabi|royalty parent married nature leader
''')
group('Disney classics','animated film','fictional animation film fantasy adventure musical', '''
Aladdin|Aladdin (Disney character)|poor hero romance magic adventure secret-identity orphan
Jasmine|Jasmine (Aladdin)|royalty romance rebel castle nature royal-heir
Genie|Genie (Disney)|blue magic nonhuman shapeshift immortal comedy flight
Jafar|Jafar (Aladdin)|villain magic royal-adviser sword leader betrayal
Ariel|Ariel (The Little Mermaid)|royalty underwater transformation romance sibling singer
Ursula|Ursula (The Little Mermaid)|villain magic underwater shapeshift singer
Belle|Belle (Beauty and the Beast)|romance castle bookish parent poor hero
Beast|Beast (Beauty and the Beast)|royalty monster transformation castle romance wealthy
Gaston|Gaston (Beauty and the Beast)|villain athlete combat weapon rival
Mulan|Mulan (Disney character)|hero sword military secret-identity parent horse combat
Mushu|Mushu (Mulan)|dragon small magic sidekick fire comedy
Pocahontas|Pocahontas (1995 film character)|nature animal-lover romance forest hero
Moana|Moana (character)|royalty water island adventure hero search ocean
Maui|Maui (Moana)|magic shapeshift giant tattoo hero combat trickster
Rapunzel|Rapunzel (Tangled)|royalty magic long-hair castle isolation romance artist
Flynn Rider|Flynn Rider|criminal thief romance secret-identity comedy adventure
Mother Gothel|Mother Gothel|villain magic long-hair deception parent isolation
Maleficent|Maleficent|villain magic horned cape flight dragon transformation
Cruella de Vil|Cruella de Vil|villain wealthy costume animal obsession car
Peter Pan|Peter Pan (Disney film)|flight sword island young leader fantasy
Captain Hook|Captain Hook|pirate villain sword hat vehicle revenge rival
Tinker Bell|Tinker Bell|magic flight small green forest friendship
''')
group('Pixar films','animated film','fictional animation film adventure comedy family', '''
Mike Wazowski|Mike Wazowski|green monster nonhuman small friend leader competition
Sulley|James P. Sullivan|blue monster giant hero parent mentor friendship
Randall Boggs|Randall Boggs|purple monster villain shapeshift betrayal
Lightning McQueen|Lightning McQueen|red artificial vehicle athlete competition rival
Mater|Mater (Cars)|artificial vehicle sidekick friend comedy
Remy|Remy (Ratatouille)|animal small chef restaurant adventure friendship
Linguini|Alfredo Linguini|chef family-business poor restaurant comedy
WALL-E|WALL-E (character)|robot artificial space technology romance survival
EVE|EVE (WALL-E)|robot artificial flight space technology romance
Joy|Joy (Inside Out)|yellow nonhuman identity leader friendship
Sadness|Sadness (Inside Out)|blue nonhuman identity friendship
Anger|Anger (Inside Out)|red nonhuman fire identity comedy
Miguel Rivera|Miguel (Coco)|musician musical-instrument singer family search young
Héctor|Héctor (Coco)|undead musician musical-instrument family redemption betrayal
Merida|Merida (Brave)|royalty bow horse forest rebel castle
''')
group('SpongeBob SquarePants','animated television','fictional animation television comedy underwater animal', '''
SpongeBob SquarePants|SpongeBob SquarePants (character)|yellow chef small animal talking-animal friendship school
Patrick Star|Patrick Star|pink talking-animal small friendship comedy lazy
Squidward Tentacles|Squidward Tentacles|blue musician musical-instrument artist teacher neighbour
Mr. Krabs|Mr. Krabs|red entrepreneur wealthy chef parent military
Sandy Cheeks|Sandy Cheeks|scientist inventor martial-arts animal talking-animal technology
Plankton|Plankton (SpongeBob SquarePants)|green scientist inventor villain small entrepreneur
Karen Plankton|Karen Plankton|robot artificial technology scientist spouse
Pearl Krabs|Pearl Krabs|animal talking-animal student young parent family
Mrs. Puff|Mrs. Puff|teacher school animal talking-animal vehicle-driver
Gary the Snail|Gary the Snail|animal pet small friendship
''')
group('The Simpsons','animated television','fictional animation television comedy', '''
Homer Simpson|Homer Simpson|yellow parent married bald nuclear-power workplace
Marge Simpson|Marge Simpson|blue long-hair parent married family
Bart Simpson|Bart Simpson|yellow student school trickster sibling skateboard
Lisa Simpson|Lisa Simpson|yellow student school musician musical-instrument activist
Maggie Simpson|Maggie Simpson|yellow small young sibling
Mr. Burns|Mr. Burns|bald wealthy villain entrepreneur leader elder
Ned Flanders|Ned Flanders|glasses facial-hair parent married religion
Milhouse Van Houten|Milhouse Van Houten|glasses student young friendship school
Krusty the Clown|Krusty the Clown|actor wealthy performer costume parent
Chief Wiggum|Chief Wiggum|law parent leader gun comedy
Comic Book Guy|Comic Book Guy|glasses facial-hair entrepreneur comics wealthy
Sideshow Bob|Sideshow Bob|villain criminal prison revenge actor long-hair
Moe Szyslak|Moe Szyslak|entrepreneur lonely comedy bar
Apu Nahasapeemapetilon|Apu Nahasapeemapetilon|entrepreneur family-business parent married chef
Professor Frink|Professor Frink|scientist inventor glasses laboratory technology
''')
group('Futurama','animated television','fictional animation television comedy sci-fi space technology', '''
Philip J. Fry|Philip J. Fry|time-travel poor hero romance adventure orphan
Turanga Leela|Turanga Leela|combat orphan space leader romance vehicle-driver
Bender|Bender (Futurama)|robot artificial criminal trickster chef wealthy
Professor Farnsworth|Professor Farnsworth|scientist inventor elder laboratory leader
Dr. Zoidberg|Zoidberg|alien nonhuman doctor poor underwater comedy
Amy Wong|Amy Wong|scientist student wealthy space romance
Hermes Conrad|Hermes Conrad|leader parent athlete sport competition
Zapp Brannigan|Zapp Brannigan|military leader space spacecraft comedy
Nibbler|Nibbler (Futurama)|alien nonhuman small pet secret-identity immortal
Calculon|Calculon|robot actor artificial romance television
''')
group('Adventure Time','animated television','fictional animation television fantasy adventure magic', '''
Finn the Human|Finn the Human|hero sword combat orphan young romance
Jake the Dog|Jake the Dog|animal talking-animal shapeshift parent married friendship
Princess Bubblegum|Princess Bubblegum|royalty scientist inventor pink leader laboratory
Marceline|Marceline the Vampire Queen|undead flight musician musical-instrument singer romance immortal
Ice King|Ice King|blue ice magic royalty villain redemption isolation
BMO|BMO (Adventure Time)|robot artificial video-game small friendship
Flame Princess|Flame Princess|royalty fire magic romance leader
Lumpy Space Princess|Lumpy Space Princess|purple royalty alien shapeshift comedy
The Lich|The Lich (Adventure Time)|undead villain magic resurrection monster
Lady Rainicorn|Lady Rainicorn|animal magic flight parent romance
''')
group('Avatar: The Last Airbender','animated television','fictional animation television fantasy martial-arts adventure', '''
Aang|Aang|air flight magic chosen-one young mentor ice nature
Katara|Katara (Avatar: The Last Airbender)|water ice magic healer sibling mentor
Sokka|Sokka|sword weapon comedy leader sibling inventor
Toph Beifong|Toph Beifong|earth magic combat teacher wealthy inventor
Zuko|Zuko|fire royalty scar sword redemption betrayal royal-heir
Iroh|Iroh|fire royalty elder mentor military tea leader
Azula|Azula|blue fire lightning royalty villain sibling leadership-conflict
Appa|Appa (Avatar: The Last Airbender)|animal flight pet giant friendship
Ty Lee|Ty Lee|combat acrobat martial-arts young friend
Suki|Suki (Avatar: The Last Airbender)|combat leader mask martial-arts romance
''')
group('Pokémon','video game and animation','fictional video-game animation television fantasy adventure competition', '''
Pikachu|Pikachu|yellow animal nonhuman lightning small pet friendship
Charizard|Charizard|orange dragon flight fire giant combat
Bulbasaur|Bulbasaur|green animal nonhuman nature forest plant
Squirtle|Squirtle|blue animal nonhuman water small underwater
Mewtwo|Mewtwo|purple artificial telepathy psychic lab villain redemption
Meowth|Meowth (Pokémon)|animal talking-animal villain comedy team
Eevee|Eevee|animal nonhuman small pet transformation
Gengar|Gengar|purple ghost monster supernatural shapeshift
Lucario|Lucario|blue animal nonhuman martial-arts telepathy combat
Jigglypuff|Jigglypuff|pink animal nonhuman singer small musical
Ash Ketchum|Ash Ketchum|hat student pet competition young friendship
Misty|Misty (Pokémon)|water athlete mentor pet competition
Brock|Brock (Pokémon)|chef mentor pet parent athlete
Jessie|Jessie (Team Rocket)|villain criminal actor team costume
James|James (Team Rocket)|villain criminal wealthy team costume
''')
group('Super Mario','video game','fictional video-game fantasy adventure comedy', '''
Mario|Mario|red hat facial-hair hero chef vehicle-driver sibling
Luigi|Luigi|green hat facial-hair hero sibling ghost combat
Princess Peach|Princess Peach|pink royalty leader castle hero romance
Bowser|Bowser|villain giant monster fire parent royalty castle
Toad|Toad (Nintendo)|small hat nonhuman sidekick royal-adviser
Yoshi|Yoshi|green animal nonhuman dinosaur sidekick pet
Princess Daisy|Princess Daisy|yellow royalty leader castle athlete
Wario|Wario|yellow hat facial-hair wealthy villain antihero rival
Waluigi|Waluigi|purple hat facial-hair rival athlete competition
Rosalina|Rosalina (Mario)|royalty magic space mother mentor
Donkey Kong|Donkey Kong (character)|animal nonhuman giant hero athlete
Diddy Kong|Diddy Kong|animal nonhuman small hat sidekick friendship
''')
group('The Legend of Zelda','video game','fictional video-game fantasy magic adventure sword', '''
Link|Link (The Legend of Zelda)|green hat sword combat hero chosen-one orphan horse
Princess Zelda|Princess Zelda|royalty magic leader castle chosen-one bow
Ganondorf|Ganon|villain magic royalty giant sword betrayal leadership-conflict
Impa|Impa|mentor combat martial-arts royal-adviser elder
Midna|Midna|magic shapeshift royalty small leadership-conflict
Tingle|Tingle (character)|green comedy flight map explorer
Skull Kid|Skull Kid|mask magic forest villain redemption
Revali|Revali|animal talking-animal flight bow rival hero
Mipha|Mipha|royalty underwater water healer romance
Daruk|Daruk|giant fire combat hero mentor
Urbosa|Urbosa|royalty lightning combat leader sword
''')
group('Sonic the Hedgehog','video game and animation','fictional video-game animation sci-fi adventure animal talking-animal', '''
Sonic|Sonic the Hedgehog|blue hero athlete speed rival
Tails|Tails (Sonic the Hedgehog)|yellow flight inventor scientist technology sidekick
Knuckles|Knuckles the Echidna|red combat super-strength guardian island
Amy Rose|Amy Rose|pink hero weapon romance adventure
Shadow|Shadow the Hedgehog|black red antihero artificial technology rival immortal
Rouge|Rouge the Bat|spy flight criminal treasure hunter
Dr. Eggman|Doctor Eggman|bald facial-hair scientist inventor villain robot
Silver|Silver the Hedgehog|white telepathy time-travel hero
Cream|Cream the Rabbit|animal flight young pet friendship
Metal Sonic|Metal Sonic|blue robot artificial villain technology
''')
group('Minecraft','video game','fictional video-game fantasy adventure survival', '''
Steve|Steve (Minecraft)|hero explorer crafting technology-inventor combat
Alex|Alex (Minecraft)|hero explorer forest survival combat
Creeper|Creeper (Minecraft)|green monster explosive villain
Enderman|Enderman|black monster nonhuman teleportation giant
Zombie|Zombie (Minecraft)|green monster undead villain
Skeleton|Skeleton (Minecraft)|undead monster bow combat
Ender Dragon|Ender Dragon|dragon giant flight monster
Villager|Villager (Minecraft)|entrepreneur chef village family-business
Iron Golem|Iron Golem|artificial giant hero combat village
Warden|Warden (Minecraft)|monster giant dark underwater
''')
group('Harry Potter','novel and film','fictional novel film fantasy school wizard magic', '''
Harry Potter|Harry Potter (character)|glasses orphan scar chosen-one student sword mentor friendship
Hermione Granger|Hermione Granger|student hero activist mystery friendship school mentor
Ron Weasley|Ron Weasley|student sibling poor hero friendship family
Albus Dumbledore|Albus Dumbledore|elder teacher mentor leader facial-hair castle
Severus Snape|Severus Snape|teacher spy betrayal redemption double-life identity
Lord Voldemort|Lord Voldemort|villain bald immortality undead orphan transformation
Draco Malfoy|Draco Malfoy|student wealthy rival redemption parent
Luna Lovegood|Luna Lovegood|student glasses nature friendship animal-lover
Neville Longbottom|Neville Longbottom|student teacher orphan sword plant nature
Rubeus Hagrid|Rubeus Hagrid|teacher giant animal-lover pet forest facial-hair
Sirius Black|Sirius Black|prison shapeshift mentor escape orphan
Remus Lupin|Remus Lupin|teacher monster shapeshift mentor parent
Bellatrix Lestrange|Bellatrix Lestrange|villain criminal prison betrayal magic
Minerva McGonagall|Minerva McGonagall|teacher mentor shapeshift castle leader
Dobby|Dobby (Harry Potter)|small nonhuman magic hero freedom
Ginny Weasley|Ginny Weasley|student athlete romance sibling combat
Cedric Diggory|Cedric Diggory|student athlete competition death hero
Professor Quirrell|Quirinus Quirrell|teacher villain hat secret-identity betrayal
''')
group('The Lord of the Rings','novel and film','fictional novel film fantasy adventure quest sword', '''
Frodo Baggins|Frodo Baggins|small hero orphan forest isolation search
Samwise Gamgee|Samwise Gamgee|small hero parent friendship garden nature
Gandalf|Gandalf|wizard magic mentor facial-hair hat elder resurrection
Aragorn|Aragorn|royalty sword combat leader romance royal-heir
Legolas|Legolas|royalty bow forest immortal combat leader
Gimli|Gimli (Middle-earth)|small facial-hair axe combat friendship
Gollum|Gollum|small monster transformation double-life betrayal search
Boromir|Boromir|sword military betrayal redemption parent family
Galadriel|Galadriel|royalty magic immortal leader forest elder
Saruman|Saruman|wizard magic villain facial-hair leader betrayal
Éowyn|Éowyn|royalty sword horse combat hero romance
Faramir|Faramir|royalty bow military romance sibling
Bilbo Baggins|Bilbo Baggins|small explorer immortal quest wealthy
Treebeard|Treebeard|nonhuman giant nature forest elder leader
''')
group('Star Wars','film and television','fictional film television sci-fi space spacecraft wartime', '''
Luke Skywalker|Luke Skywalker|magic sword orphan hero chosen-one mentor sibling
Leia Organa|Princess Leia|royalty leader rebel gun sibling parent
Darth Vader|Darth Vader|mask cape villain sword magic parent redemption transformation
Han Solo|Han Solo|pilot gun criminal rebel romance parent vehicle-driver
Chewbacca|Chewbacca|alien giant facial-hair weapon pilot friendship
Yoda|Yoda|green small magic mentor elder sword nature
Obi-Wan Kenobi|Obi-Wan Kenobi|magic mentor sword elder betrayal
R2-D2|R2-D2|robot artificial technology vehicle friendship
C-3PO|C-3PO|robot artificial technology comedy translation
Padmé Amidala|Padmé Amidala|royalty politician romance parent leader
Ahsoka Tano|Ahsoka Tano|magic sword rebel apprentice hero
Darth Maul|Darth Maul|red villain sword mask revenge resurrection
Boba Fett|Boba Fett|mask armor gun criminal vehicle-driver survival
The Mandalorian|The Mandalorian (character)|mask armor gun parent bounty hunter
Grogu|Grogu|green small magic young student mentor
Rey|Rey (Star Wars)|magic sword orphan hero chosen-one search
Kylo Ren|Kylo Ren|mask sword magic villain redemption parent
Jabba the Hutt|Jabba the Hutt|alien giant criminal wealthy leader
Grand Admiral Thrawn|Grand Admiral Thrawn|blue alien military leader strategist
Admiral Ackbar|Admiral Ackbar|alien military leader rebel underwater
''')
group('Marvel','comics and film','fictional comics film superhero sci-fi action combat', '''
Spider-Man|Spider-Man|mask secret-identity orphan hero technology scientist
Iron Man|Iron Man|armor wealthy inventor technology flight hero parent
Captain America|Captain America|blue red mask military hero shield leader
Thor|Thor (Marvel Comics)|royalty lightning magic flight hammer sibling
Hulk|Hulk|green giant super-strength transformation scientist alter-ego
Black Widow|Black Widow (Natasha Romanova)|spy gun martial-arts orphan double-life
Hawkeye|Hawkeye (Clint Barton)|bow weapon parent mentor team
Black Panther|Black Panther (character)|royalty black suit leader technology combat
Doctor Strange|Doctor Strange|doctor magic cape mentor time-travel
Scarlet Witch|Scarlet Witch|red magic telepathy sibling parent reality transformation
Vision|Vision (Marvel Comics)|robot artificial red flight telepathy technology
Loki|Loki (Marvel Comics)|green magic trickster royalty shapeshift villain redemption
Ant-Man|Ant-Man (Scott Lang)|mask small technology transformation parent criminal
Wasp|Wasp (comics)|flight small technology scientist hero
Star-Lord|Star-Lord|space gun pilot parent musical-instrument technology
Gamora|Gamora|green alien sword martial-arts orphan redemption
Rocket Raccoon|Rocket Raccoon|animal talking-animal gun inventor space
Groot|Groot|nature tree nonhuman giant regeneration
Drax|Drax the Destroyer|alien giant super-strength revenge parent
Thanos|Thanos|purple alien giant villain parent leadership-conflict
Deadpool|Deadpool|red mask antihero sword gun immortality comedy
Wolverine|Wolverine (character)|scar metal claws combat immortal antihero orphan
Storm|Storm (Marvel Comics)|flight lightning weather royalty leader
Professor X|Professor X|bald telepathy scientist mentor leader
Magneto|Magneto (Marvel Comics)|helmet villain antihero leader technology wartime
Mystique|Mystique (character)|blue shapeshift spy villain parent
Nightcrawler|Nightcrawler (character)|blue teleportation combat religion romance
Jean Grey|Jean Grey|red telepathy flight resurrection superhero
Daredevil|Daredevil (Marvel Comics character)|red mask law martial-arts orphan
Kingpin|Kingpin (character)|bald wealthy villain criminal leader super-strength
Green Goblin|Green Goblin|green mask villain scientist inventor flight
Ms. Marvel|Kamala Khan|young shapeshift student hero identity
Moon Knight|Moon Knight|mask cape antihero double-life magic
Shang-Chi|Shang-Chi|martial-arts combat family betrayal magic
''')
group('DC Comics','comics and film','fictional comics film superhero sci-fi action combat', '''
Batman|Batman|mask cape secret-identity orphan wealthy detective technology
Superman|Superman|blue red cape alien flight super-strength secret-identity parent
Wonder Woman|Wonder Woman|royalty magic sword combat leader flight
The Flash|Flash (DC Comics character)|red mask speed science time-travel hero
Aquaman|Aquaman|royalty underwater water animal-lover leader
Green Lantern|Green Lantern|green mask space technology flight leader
Joker|Joker (character)|villain criminal clown costume trickster rival
Harley Quinn|Harley Quinn|red black villain antihero doctor costume criminal
Catwoman|Catwoman|mask thief criminal antihero romance secret-identity
Robin|Robin (character)|mask sidekick orphan acrobat hero
Batgirl|Batgirl|mask detective secret-identity student martial-arts
Alfred Pennyworth|Alfred Pennyworth|mentor facial-hair parent royal-adviser combat
Riddler|Riddler|green hat villain mystery criminal detective-fiction
Penguin|Penguin (character)|hat villain wealthy criminal entrepreneur
Two-Face|Two-Face|scar villain law criminal double-life
Poison Ivy|Poison Ivy (character)|green nature scientist villain magic
Lex Luthor|Lex Luthor|bald wealthy scientist inventor politician villain
Darkseid|Darkseid|alien giant villain leader royalty immortal
Cyborg|Cyborg (DC Comics)|robot artificial technology super-strength hero
Raven|Raven (DC Comics)|magic cape supernatural telepathy parent
Beast Boy|Beast Boy|green shapeshift animal hero comedy young
Shazam|Captain Marvel (DC Comics)|red cape magic transformation young flight
Zatanna|Zatanna|magic hat performer musician costume
John Constantine|John Constantine|magic detective facial-hair antihero supernatural
Deathstroke|Deathstroke|mask sword gun villain antihero military
''')
group('A Song of Ice and Fire / Game of Thrones','novel and television','fictional novel television fantasy wartime leadership-conflict', '''
Jon Snow|Jon Snow (character)|sword orphan hero resurrection leader animal-lover
Daenerys Targaryen|Daenerys Targaryen|dragon fire leader exile royal-heir
Tyrion Lannister|Tyrion Lannister|small royal-adviser witty prison betrayal family
Cersei Lannister|Cersei Lannister|villain leader parent sibling romance wealthy
Jaime Lannister|Jaime Lannister|sword combat parent romance sibling redemption
Arya Stark|Arya Stark|sword shapeshift orphan revenge secret-identity
Sansa Stark|Sansa Stark|leader orphan royalty prison romance
Bran Stark|Bran Stark|telepathy magic prophecy chosen-one sibling
Sandor Clegane|Sandor Clegane|scar sword combat villain redemption fire
Brienne of Tarth|Brienne of Tarth|sword armor combat hero leader
Petyr Baelish|Petyr Baelish|villain spy wealthy betrayal royal-adviser
Varys|Varys|bald spy royal-adviser betrayal leader
Melisandre|Melisandre|red magic resurrection prophecy elder
Theon Greyjoy|Theon Greyjoy|royalty betrayal prison redemption sibling
Oberyn Martell|Oberyn Martell|royalty sword combat revenge romance
''')
group('Doctor Who','television','fictional television sci-fi time-travel space adventure', '''
The Doctor|The Doctor (Doctor Who)|alien regeneration mentor hero technology double-life
Rose Tyler|Rose Tyler|hero romance travel alternate-universe
Martha Jones|Martha Jones|doctor hero survival technology
Donna Noble|Donna Noble|comedy hero identity family
Amy Pond|Amy Pond|romance family time-travel search
Rory Williams|Rory Williams|doctor married parent romance resurrection
River Song|River Song (Doctor Who)|spy gun secret-identity romance resurrection
The Master|The Master (Doctor Who)|alien villain shapeshift time-travel double-life
Davros|Davros|scientist inventor villain artificial technology
K-9|K-9 (Doctor Who)|robot animal artificial pet technology
Captain Jack Harkness|Jack Harkness|gun immortal time-travel leader romance
Clara Oswald|Clara Oswald|teacher student magic identity resurrection
The Daleks|Dalek|robot artificial alien technology weapon villain
''')
group('Star Trek','television and film','fictional television film sci-fi space spacecraft technology', '''
James T. Kirk|James T. Kirk|military leader explorer vehicle-driver gun
Spock|Spock|alien scientist mentor telepathy leader
Leonard McCoy|Leonard McCoy|doctor scientist mentor gun
Nyota Uhura|Nyota Uhura|military singer musician leader
Montgomery Scott|Montgomery Scott|inventor scientist technology vehicle-driver
Jean-Luc Picard|Jean-Luc Picard|bald leader military explorer mentor
Data|Data (Star Trek)|robot artificial scientist technology musician
Worf|Worf|alien military sword combat parent
Seven of Nine|Seven of Nine|artificial technology scientist identity
Kathryn Janeway|Kathryn Janeway|military leader scientist explorer
Benjamin Sisko|Benjamin Sisko|military leader parent wartime mentor
Quark|Quark (Star Trek)|alien entrepreneur wealthy criminal comedy
''')
group('Horror films','film','fictional film horror supernatural survival', '''
Dracula|Count Dracula|undead monster shapeshift immortal romance castle
Frankenstein’s Monster|Frankenstein's monster|artificial monster giant scar isolation resurrection
Freddy Krueger|Freddy Krueger|scar undead villain magic dream revenge
Jason Voorhees|Jason Voorhees|mask giant villain weapon immortal
Michael Myers|Michael Myers (Halloween)|mask villain weapon prison silent
Ghostface|Ghostface (identity)|mask villain gun weapon secret-identity mystery
Chucky|Chucky (character)|artificial small villain criminal supernatural
Pennywise|It (character)|clown shapeshift alien monster fear
Samara Morgan|Samara Morgan|ghost undead villain supernatural young
Norman Bates|Norman Bates|criminal villain double-life family mystery
Hannibal Lecter|Hannibal Lecter|doctor villain criminal prison chef
Carrie White|Carrie White|telepathy magic student revenge parent
''')
group('Classic literature','novel','fictional novel literature adventure', '''
Sherlock Holmes|Sherlock Holmes|detective violin musician mystery technology
Dr. Watson|Dr. Watson|doctor military writer mentor detective
Professor Moriarty|Professor Moriarty|villain criminal scientist leader detective-fiction
Alice|Alice (Alice's Adventures in Wonderland)|young transformation travel nature search
Mad Hatter|Hatter (Alice's Adventures in Wonderland)|hat comedy trickster tea
Cheshire Cat|Cheshire Cat|animal talking-animal shapeshift trickster magic
Queen of Hearts|Queen of Hearts (Alice's Adventures in Wonderland)|royalty villain leader castle
Dorothy Gale|Dorothy Gale|young orphan search magic pet friendship
Scarecrow|Scarecrow (Oz)|artificial nonhuman mentor search friendship
Tin Woodman|Tin Woodman|robot artificial sword search friendship
Cowardly Lion|Cowardly Lion|animal talking-animal royalty courage search
Wicked Witch of the West|Wicked Witch of the West|witch magic villain flight castle
Ebenezer Scrooge|Ebenezer Scrooge|wealthy elderly redemption ghost isolation
Oliver Twist|Oliver Twist|orphan poor young criminal survival
Long John Silver|Long John Silver|pirate criminal sword betrayal island
Captain Ahab|Captain Ahab|leader revenge vehicle-driver sea scar
Jay Gatsby|Jay Gatsby|wealthy secret-identity romance party criminal
Atticus Finch|Atticus Finch|law parent mentor court southern
Elizabeth Bennet|Elizabeth Bennet|sibling romance poor family married
Mr. Darcy|Fitzwilliam Darcy|wealthy romance family married
Hester Prynne|Hester Prynne|scar parent identity isolation romance
''')
group('Shakespeare','theatre and literature','fictional theatre novel romance betrayal', '''
Hamlet|Prince Hamlet|royalty sword revenge ghost orphan royal-heir
Ophelia|Ophelia|romance family parent madness
Claudius|King Claudius|royalty villain betrayal parent leader
Macbeth|Macbeth (character)|royalty sword military villain prophecy betrayal
Lady Macbeth|Lady Macbeth|royalty villain betrayal leadership-conflict married
Romeo|Romeo Montague|romance sword rivalry young family
Juliet|Juliet|romance young family royalty secrecy
Othello|Othello|military leader betrayal romance sword
Iago|Iago|villain betrayal spy military revenge
King Lear|King Lear|royalty elder parent betrayal leadership-conflict
Puck|Puck (A Midsummer Night's Dream)|magic trickster forest shapeshift comedy
Prospero|Prospero|magic wizard parent island revenge mentor
Caliban|Caliban|monster island survival nature betrayal
Falstaff|Falstaff|facial-hair comedy military wealthy mentor
''')
group('Mythology and folklore','mythology','fictional folklore fantasy supernatural magic', '''
Zeus|Zeus|royalty lightning shapeshift parent leader immortal
Hera|Hera|royalty parent married revenge immortal leadership-conflict
Athena|Athena|royalty sword mentor combat immortal owl
Poseidon|Poseidon|royalty water underwater horse parent immortal
Hades|Hades|royalty undead castle leader immortal
Hermes|Hermes|flight hat trickster mentor travel immortal
Aphrodite|Aphrodite|romance royalty immortal parent magic
Medusa|Medusa|monster scar snake transformation supernatural
Hercules|Heracles|giant super-strength hero parent revenge combat
Achilles|Achilles|sword military combat revenge wartime prophecy
Odysseus|Odysseus|sword explorer trickster parent travel island
Perseus|Perseus|sword hero monster combat royalty
Anansi|Anansi|animal talking-animal trickster storytelling nature
Loki (Norse)|Loki|magic trickster shapeshift parent giant betrayal
Thor (Norse)|Thor|lightning super-strength weapon royalty giant
Odin|Odin|royalty magic parent elder leader prophecy
Fenrir|Fenrir|animal monster giant prophecy parent
Baba Yaga|Baba Yaga|wizard forest elder flight house
Robin Hood|Robin Hood|bow hero criminal forest poor rebel
King Arthur|King Arthur|royalty sword leader castle magic prophecy
Merlin|Merlin|wizard mentor magic elder prophecy castle
Morgana|Morgan le Fay|magic royalty villain shapeshift betrayal
Beowulf|Beowulf|sword hero leader monster combat
''')
group('Indie and other video games','video game','fictional video-game adventure combat', '''
Lara Croft|Lara Croft|explorer gun wealthy orphan survival archaeology
Nathan Drake|Nathan Drake (Uncharted)|explorer gun orphan travel wealthy
Kratos|Kratos (God of War)|sword weapon parent royalty revenge combat
Atreus|Atreus (God of War)|bow magic parent orphan young
Aloy|Aloy|bow orphan technology explorer nature combat
Ellie|Ellie (The Last of Us)|young survival gun musician musical-instrument orphan
Joel Miller|Joel (The Last of Us)|parent gun survival mentor betrayal
Geralt of Rivia|Geralt of Rivia|sword magic monster hunter parent mentor
Ciri|Ciri|royalty sword magic time-travel young chosen-one
Yennefer|Yennefer of Vengerberg|magic wizard romance parent transformation
Cloud Strife|Cloud Strife|sword military orphan secret-identity identity
Sephiroth|Sephiroth (Final Fantasy)|sword villain long-hair magic space
Tifa Lockhart|Tifa Lockhart|martial-arts combat orphan romance
Aerith Gainsborough|Aerith Gainsborough|magic nature romance orphan sacrifice
Samus Aran|Samus Aran|armor gun space orphan bounty hunter technology
Solid Snake|Solid Snake|spy gun military secret-identity clone technology
Big Boss|Big Boss (Metal Gear)|spy gun military leader betrayal parent
Master Chief|Master Chief (Halo)|armor gun military space technology
Cortana|Cortana (Halo)|robot artificial technology telepathy space
Doom Slayer|Doom Slayer|armor gun monster combat space
GLaDOS|GLaDOS|robot artificial villain scientist technology laboratory
Chell|Chell (Portal)|science laboratory survival technology silent
Sans|Sans (Undertale)|undead small comedy magic telepathy
Papyrus|Papyrus (Undertale)|undead comedy magic chef sibling
Frisk|Frisk (Undertale)|young hero survival identity friendship
Cuphead|Cuphead (character)|artificial young comedy gun devil
Mugman|Mugman|artificial young comedy gun sibling
Madeline|Madeline (Celeste)|young survival nature search mountain
The Knight|The Knight (Hollow Knight)|mask sword small nonhuman explorer
Hornet|Hornet (Hollow Knight)|mask sword nonhuman royalty hero
''')
group('Anime and manga','manga and anime','fictional animation television comics japanese fantasy action', '''
Goku|Goku|martial-arts alien flight super-strength parent transformation
Vegeta|Vegeta|royalty alien flight villain redemption parent rival
Piccolo|Piccolo (Dragon Ball)|green alien mentor flight regeneration combat
Bulma|Bulma|scientist inventor wealthy technology parent
Frieza|Frieza|purple alien shapeshift villain flight immortality
Naruto Uzumaki|Naruto Uzumaki|orphan hero leader magic parent transformation
Sasuke Uchiha|Sasuke Uchiha|sword orphan revenge villain redemption lightning
Sakura Haruno|Sakura Haruno|doctor super-strength teacher magic parent
Kakashi Hatake|Kakashi Hatake|mask teacher mentor lightning magic scar
Itachi Uchiha|Itachi Uchiha|spy betrayal sibling secret-identity redemption
Monkey D. Luffy|Monkey D. Luffy|hat pirate leader shapeshift hero parent
Roronoa Zoro|Roronoa Zoro|sword pirate combat scar loyalty
Nami|Nami (One Piece)|pirate navigation thief weather orphan
Sanji|Sanji (One Piece)|chef pirate martial-arts romance orphan
Tony Tony Chopper|Tony Tony Chopper|animal talking-animal doctor hat shapeshift pirate
Nico Robin|Nico Robin|archaeology orphan pirate mystery knowledge
Usopp|Usopp|pirate inventor weapon comedy parent
Trafalgar Law|Trafalgar D. Water Law|pirate sword doctor hat magic
Light Yagami|Light Yagami|student villain secret-identity criminal double-life
L|L (Death Note)|detective mystery orphan rivalry genius
Ryuk|Ryuk (Death Note)|nonhuman monster magic immortal flight
Misa Amane|Misa Amane|singer actor secret-identity romance double-life
Edward Elric|Edward Elric|science magic artificial arm sibling orphan
Alphonse Elric|Alphonse Elric|artificial armor nonhuman sibling orphan
Roy Mustang|Roy Mustang|fire military leader magic mentor
Winry Rockbell|Winry Rockbell|inventor technology orphan mechanic
Sailor Moon|Usagi Tsukino|magic transformation student superhero romance
Sailor Mercury|Ami Mizuno|blue water magic student scientist hero
Sailor Mars|Rei Hino|red fire magic student supernatural shrine
Sailor Jupiter|Makoto Kino|green lightning magic student combat
Sailor Venus|Minako Aino|yellow magic student singer romance
Inuyasha|Inuyasha (character)|sword nonhuman romance transformation immortal
Kagome Higurashi|Kagome Higurashi|bow time-travel student romance magic
Totoro|Totoro|giant animal nonhuman magic nature forest
Kiki|Kiki (Kiki's Delivery Service)|wizard flight pet student magic
Howl|Howl (Howl's Moving Castle)|wizard shapeshift romance magic castle
Sophie Hatter|Sophie Hatter|hat transformation magic elder romance
No-Face|No-Face (Spirited Away)|mask ghost shapeshift nonhuman magic
Chihiro|Chihiro Ogino|young magic family search survival
''')
group('Television drama and comedy','television','fictional television drama', '''
Michael Scott|Michael Scott (The Office)|leader entrepreneur comedy romance actor
Dwight Schrute|Dwight Schrute|entrepreneur farmer leader combat rival
Jim Halpert|Jim Halpert|parent married trickster entrepreneur friendship
Pam Beesly|Pam Beesly|artist parent married office romance
Leslie Knope|Leslie Knope|politician leader activist mentor entrepreneur
Ron Swanson|Ron Swanson|facial-hair leader inventor entrepreneur chef
April Ludgate|April Ludgate|animal-lover comedy married entrepreneur
Andy Dwyer|Andy Dwyer|musician singer comedy married parent
Walter White|Walter White (Breaking Bad)|teacher scientist criminal bald villain parent double-life
Jesse Pinkman|Jesse Pinkman|criminal student poor redemption parent
Saul Goodman|Saul Goodman|law criminal secret-identity entrepreneur court
Gus Fring|Gus Fring|chef entrepreneur villain criminal leader double-life
Mike Ehrmantraut|Mike Ehrmantraut|gun criminal law parent mentor
Eleven|Eleven (Stranger Things)|telepathy young orphan science laboratory supernatural
Dustin Henderson|Dustin Henderson|hat student science technology friendship
Steve Harrington|Steve Harrington|mentor parent friendship combat
Jim Hopper|Jim Hopper (Stranger Things)|law gun parent survival
Wednesday Addams|Wednesday Addams|student detective supernatural mystery family
Gomez Addams|Gomez Addams|facial-hair wealthy sword parent married
Morticia Addams|Morticia Addams|long-hair wealthy parent married supernatural
Uncle Fester|Uncle Fester|bald lightning supernatural family comedy
''')
group('The Muppets and Sesame Street','puppetry and television','fictional television comedy musical', '''
Kermit the Frog|Kermit the Frog|green animal talking-animal leader singer musician romance
Miss Piggy|Miss Piggy|pink animal talking-animal singer actor combat romance costume
Fozzie Bear|Fozzie Bear|animal talking-animal hat singer friendship comedy
Gonzo|Gonzo (Muppet)|blue actor stunt performer nonhuman romance
Animal|Animal (Muppet)|red musician musical-instrument drums comedy
Rowlf the Dog|Rowlf the Dog|animal talking-animal musician musical-instrument singer
Swedish Chef|Swedish Chef|chef hat comedy musical
Statler|Statler and Waldorf|elder comedy critic rivalry
Waldorf|Statler and Waldorf|elder comedy critic rivalry
Big Bird|Big Bird|yellow giant animal talking-animal young mentor singer
Elmo|Elmo|red small monster young friendship
Cookie Monster|Cookie Monster|blue monster chef comedy
Oscar the Grouch|Oscar the Grouch|green monster small comedy poor
Count von Count|Count von Count|purple undead monster math number
Grover|Grover|blue monster small hero comedy
Bert|Bert and Ernie|yellow glasses comedy roommate
Ernie|Bert and Ernie|orange comedy friendship roommate
Abby Cadabby|Abby Cadabby|pink magic flight young student
''')
group('American historical figures','history','real history historical-figure public-figure', '''
Abraham Lincoln|Abraham Lincoln|american politician leader facial-hair law assassination wartime
George Washington|George Washington|american politician military leader wartime parent
Benjamin Franklin|Benjamin Franklin|american scientist inventor writer politician glasses
Harriet Tubman|Harriet Tubman|american activist explorer survival spy wartime
Frederick Douglass|Frederick Douglass|american writer activist leader facial-hair
Susan B. Anthony|Susan B. Anthony|american activist teacher writer politician
Rosa Parks|Rosa Parks|american activist historic rebellion married
Martin Luther King Jr.|Martin Luther King Jr.|american activist religion leader award speaker
Malcolm X|Malcolm X|american activist religion glasses speaker
Amelia Earhart|Amelia Earhart|american explorer pilot vehicle-driver adventure
Neil Armstrong|Neil Armstrong|american explorer military space spacecraft vehicle-driver
Buzz Aldrin|Buzz Aldrin|american military space spacecraft explorer writer
Sally Ride|Sally Ride|american scientist space spacecraft teacher
Katherine Johnson|Katherine Johnson|american scientist technology education space
Margaret Hamilton|Margaret Hamilton (software engineer)|american scientist technology-inventor space
''')
group('Science and invention','history','real history scientist public-figure', '''
Albert Einstein|Albert Einstein|glasses facial-hair teacher writer award european
Marie Curie|Marie Curie|teacher award european french laboratory parent
Isaac Newton|Isaac Newton|teacher european scientist writer physics
Ada Lovelace|Ada Lovelace|british writer technology-inventor math parent
Alan Turing|Alan Turing|british technology-inventor wartime education mathematics
Charles Darwin|Charles Darwin|british explorer nature writer facial-hair
Nikola Tesla|Nikola Tesla|european technology-inventor electricity laboratory
Thomas Edison|Thomas Edison|american technology-inventor entrepreneur patent
Galileo Galilei|Galileo Galilei|european teacher astronomy court telescope
Jane Goodall|Jane Goodall|british nature animal-lover activist writer
Stephen Hawking|Stephen Hawking|british teacher writer award wheelchair
Rosalind Franklin|Rosalind Franklin|british laboratory physics scientist
Dmitri Mendeleev|Dmitri Mendeleev|european teacher writer facial-hair
Louis Pasteur|Louis Pasteur|french teacher laboratory doctor
Gregor Mendel|Gregor Mendel|european religion nature teacher genetics
''')
group('Artists and writers','history','real history public-figure artist', '''
Leonardo da Vinci|Leonardo da Vinci|european inventor technology-inventor scientist facial-hair
Michelangelo|Michelangelo|european artist sculpture painter
Vincent van Gogh|Vincent van Gogh|european facial-hair poor artist
Frida Kahlo|Frida Kahlo|married survival artist activist identity
Pablo Picasso|Pablo Picasso|european wealthy art painting
Salvador Dalí|Salvador Dalí|european facial-hair artist surrealist
Georgia O’Keeffe|Georgia O'Keeffe|american nature art painting
Andy Warhol|Andy Warhol|american art pop-culture media
William Shakespeare|William Shakespeare|british theatre married parent european
Jane Austen|Jane Austen|british writer european romance novel
Charles Dickens|Charles Dickens|british writer poor education parent
Agatha Christie|Agatha Christie|british mystery detective-fiction theatre
Arthur Conan Doyle|Arthur Conan Doyle|british doctor detective-fiction mystery
J. R. R. Tolkien|J. R. R. Tolkien|british teacher fantasy wartime european
J. K. Rowling|J. K. Rowling|british fantasy parent public-figure
Terry Pratchett|Terry Pratchett|british fantasy comedy award
Mary Shelley|Mary Shelley|british horror science-fiction writer romance
George Orwell|George Orwell|british wartime politician anti-authoritarian
''')
group('World history','history','real history historical-figure public-figure', '''
Cleopatra|Cleopatra|royalty leader african politician parent romance royal-heir
Julius Caesar|Julius Caesar|european military politician leader betrayal assassination
Augustus|Augustus|european military politician leader royal-heir
Joan of Arc|Joan of Arc|french military religion sword young visionary
Napoleon Bonaparte|Napoleon|french military politician leader island exile
Marie Antoinette|Marie Antoinette|french royalty parent leader royal-family
Queen Victoria|Queen Victoria|british royalty parent leader royal-family
Elizabeth I|Elizabeth I|british royalty leader royal-family theatre
Elizabeth II|Elizabeth II|british royalty parent leader royal-family
Henry VIII|Henry VIII|british royalty parent leader married royal-family
Genghis Khan|Genghis Khan|asian military leader parent horse combat
Kublai Khan|Kublai Khan|asian military leader royalty parent
Mansa Musa|Mansa Musa|african royalty wealthy leader religion
Shaka Zulu|Shaka|african military leader sword parent
Mahatma Gandhi|Mahatma Gandhi|asian activist leader writer prison
Nelson Mandela|Nelson Mandela|african activist politician leader prison award
Winston Churchill|Winston Churchill|british politician wartime leader writer award
Florence Nightingale|Florence Nightingale|british doctor wartime education writer
Boudica|Boudica|british royalty military leader sword rebel
Hatshepsut|Hatshepsut|african royalty leader parent royal-family
''')
group('Music','music','real media public-figure musician singer musical', '''
Michael Jackson|Michael Jackson|american dancer young performer award costume
Madonna|Madonna|american actor entrepreneur parent award dancer
Prince|Prince (musician)|american purple musical-instrument guitar technology-inventor
David Bowie|David Bowie|british actor costume secret-identity performer
Freddie Mercury|Freddie Mercury|british facial-hair performer award
Elton John|Elton John|british glasses musical-instrument piano costume
Taylor Swift|Taylor Swift|american writer musical-instrument guitar award
Beyoncé|Beyoncé|american dancer actor parent award entrepreneur
Lady Gaga|Lady Gaga|american actor costume piano award
Ed Sheeran|Ed Sheeran|british musical-instrument guitar award parent
Billie Eilish|Billie Eilish|american young costume award sibling
Dolly Parton|Dolly Parton|american musical-instrument guitar actor entrepreneur
Bob Marley|Bob Marley|jamaican activist musical-instrument guitar parent
Aretha Franklin|Aretha Franklin|american musical-instrument piano activist award
John Lennon|John Lennon|british musical-instrument guitar activist parent
Paul McCartney|Paul McCartney|british musical-instrument guitar parent award
Tina Turner|Tina Turner|american actor dancer award survival
Whitney Houston|Whitney Houston|american actor parent award
Kurt Cobain|Kurt Cobain|american musical-instrument guitar parent artist
Stevie Wonder|Stevie Wonder|american musical-instrument piano award blind
''')
group('Film and television celebrities','film and television','real media public-figure actor film television', '''
Charlie Chaplin|Charlie Chaplin|british american comedy hat facial-hair writer
Marilyn Monroe|Marilyn Monroe|american singer comedy romance
Audrey Hepburn|Audrey Hepburn|british dancer activist wartime award
Robin Williams|Robin Williams|american comedy singer actor award
Jim Carrey|Jim Carrey|canadian comedy artist painter
Rowan Atkinson|Rowan Atkinson|british comedy writer engineer
Dwayne Johnson|Dwayne Johnson|american athlete wrestler entrepreneur parent
Jackie Chan|Jackie Chan|asian martial-arts combat comedy singer
Keanu Reeves|Keanu Reeves|canadian musician musical-instrument motorcycle combat
Meryl Streep|Meryl Streep|american award singer parent
Samuel L. Jackson|Samuel L. Jackson|american award activist
Morgan Freeman|Morgan Freeman|american narrator award facial-hair
Tom Hanks|Tom Hanks|american award parent producer comedy musician
Whoopi Goldberg|Whoopi Goldberg|american comedy award activist
Hugh Jackman|Hugh Jackman|australian singer actor award theatre
Margot Robbie|Margot Robbie|australian award producer entrepreneur
Chris Hemsworth|Chris Hemsworth|australian parent superhero film
Emma Watson|Emma Watson|british activist education award
Daniel Radcliffe|Daniel Radcliffe|british theatre fantasy
Gordon Ramsay|Gordon Ramsay|british chef entrepreneur television parent
''')
group('Sports icons','sport','real sports athlete competition public-figure', '''
Serena Williams|Serena Williams|american parent entrepreneur award tennis
Venus Williams|Venus Williams|american entrepreneur award sibling tennis
Roger Federer|Roger Federer|european parent award tennis
Rafael Nadal|Rafael Nadal|european parent award tennis
Novak Djokovic|Novak Djokovic|european parent award tennis
Michael Jordan|Michael Jordan|american entrepreneur award basketball
LeBron James|LeBron James|american entrepreneur parent award basketball
Stephen Curry|Stephen Curry|american parent award basketball
Lionel Messi|Lionel Messi|argentinian parent award football
Cristiano Ronaldo|Cristiano Ronaldo|european entrepreneur parent award football
Pelé|Pelé|brazilian politician activist award football
Diego Maradona|Diego Maradona|argentinian parent football
Usain Bolt|Usain Bolt|jamaican award running entrepreneur
Simone Biles|Simone Biles|american gymnastics award olympics
Michael Phelps|Michael Phelps|american swimming parent award olympics
Cathy Freeman|Cathy Freeman|australian running award olympics activist
Ash Barty|Ashleigh Barty|australian tennis award cricket
Sachin Tendulkar|Sachin Tendulkar|asian cricket award parent
Virat Kohli|Virat Kohli|asian cricket award parent
Lewis Hamilton|Lewis Hamilton|british vehicle-driver racing award activist
Max Verstappen|Max Verstappen|european vehicle-driver racing award
''')
group('Children’s cartoons and comics','animated television and comic','fictional animation television comedy adventure', '''
Scooby-Doo|Scooby-Doo (character)|animal talking-animal mystery detective pet friendship
Shaggy Rogers|Shaggy Rogers|facial-hair detective pet comedy mystery
Velma Dinkley|Velma Dinkley|glasses detective student mystery
Daphne Blake|Daphne Blake|fashion detective mystery wealthy
Fred Jones|Fred Jones (Scooby-Doo)|leader detective mystery vehicle-driver
Bugs Bunny|Bugs Bunny|animal talking-animal trickster comedy hero
Daffy Duck|Daffy Duck|animal talking-animal trickster comedy villain
Tweety|Tweety|yellow animal talking-animal small pet trickster
Sylvester|Sylvester the Cat|animal talking-animal pet villain comedy
Road Runner|Road Runner (character)|animal nonhuman speed comedy
Wile E. Coyote|Wile E. Coyote and the Road Runner|animal inventor villain technology comedy
Popeye|Popeye|sailor combat super-strength facial-hair romance
Olive Oyl|Olive Oyl|romance family comedy long-hair singer costume
Garfield|Garfield|orange animal talking-animal pet comedy
Odie|Odie|yellow animal pet comedy friendship
Charlie Brown|Charlie Brown|bald student young pet friendship
Snoopy|Snoopy|animal talking-animal pet pilot vehicle-driver writer
Lucy van Pelt|Lucy van Pelt|student leader sibling comedy teacher
Linus van Pelt|Linus van Pelt|student sibling young mentor
Dennis the Menace|Dennis the Menace (U.S. comics)|young trickster student family
''')

# Correct intentional placeholder wording, common accidental duplicates, and over-confident attributes.
# These are metadata, NOT linked clues unless LINK includes the exact key.
BANNED_TAGS={'glasses?','toy','boots','loyalty','fear','snow','guardian','performer','stunt','acrobatic','acrobat','shopkeeper','restaurant','deer','pink','orange','black','white','math','number','owl','tea','critic','roommate','village','plant','cowboy','nuclear-power','workplace','skateboard','bar','physics','mathematics','electricity','astronomy','telescope','genetics','patent','art','painting','sculpture','surrealist','pop-culture','anti-authoritarian','writer?','mexican','brazilian','argentinian','jamaican','canadian','tennis','basketball','football','running','gymnastics','olympics','swimming','cricket','racing','producer','narrator','engineer','motorcycle','piano','guitar','dancer','mechanic','archaeology','navigation','clone','mountain','silent','stunt','devil','dark','psychic','healer','air','earth','plant','speed','regeneration','weather','reality','shield','hammer','alter-ego','clone','translation','bounty','translation','map','tattoo','house','ocean','escape','freedom','strat9','strategist','tea','school?','deception','garden','courage','madness','secret','violin','bookish','poetry','sacrifice','knowledge','number','scarlet','fear','genius','loyalty','identity?','translation','surrealist','horse?','witty','silent','clone','bounty hunter','tea','garden'}
# Certain legitimate and useful tags should be linked into broader categories.
SYNONYMS={'witch':'wizard','psychic':'telepathy','pilot':'vehicle-driver','mechanic':'inventor','farmer':'nature','escape':'prison','thief':'criminal','archaeology':'explorer','navigation':'explorer','guardian':'hero','researcher':'scientist','plant':'nature','ocean':'water','sea':'water','sailor':'vehicle-driver','healer':'doctor','shopkeeper':'entrepreneur','restaurant':'chef','tea':'chef','drums':'musical-instrument','piano':'musical-instrument','guitar':'musical-instrument','acrobat':'combat','stunt':'combat','clown':'costume','psychic':'telepathy','regeneration':'transformation','reality':'magic','speed':'athlete','mechanic':'inventor','bounty':'criminal','strategist':'leader','blind':'survival','science-fiction':'sci-fi','literature':'novel','manga':'comics','anime':'animation','music':'musician','sport':'athlete','action':'combat','quest':'search','healer':'doctor','investigation':'detective','technology-inventor':'inventor'}
# Propagate only implications that are generally entailed.
IMPLIES={'pirate':['weapon','adventure','vehicle-driver'],'sword':['weapon','combat'],'bow':['weapon','combat'],'gun':['weapon'],'military':['wartime'],'wizard':['magic','supernatural'],'alien':['nonhuman'],'robot':['artificial','nonhuman','technology'],'monster':['nonhuman'],'ghost':['supernatural','nonhuman'],'undead':['supernatural','nonhuman'],'talking-animal':['animal','nonhuman'],'animal':['nonhuman'],'superhero':['hero','costume'],'secret-identity':['identity','double-life'],'shapeshift':['transformation','supernatural'],'magic':['supernatural'],'time-travel':['travel'],'flight':['travel'],'royalty':['royal-court'],'royal-heir':['royalty'],'teacher':['education','mentor'],'scientist':['laboratory'],'inventor':['technology'],'doctor':[],'explorer':['travel','adventure'],'spacecraft':['space','travel'],'prison':['survival'],'orphan':['family'],'sibling':['family'],'parent':['family'],'singer':['musician','musical'],'musical-instrument':['musician'],'actor':['media'],'athlete':['sports','competition'],'spy':['secret-identity'],'criminal':['law'],'detective':['mystery'],'mystery':['detective-fiction'],'immortal':['elder'],'resurrection':['supernatural'],'lightning':['supernatural'],'fire':['supernatural'],'ice':['supernatural'],'telepathy':['supernatural'],'weapon':['combat'],'fictional':['media'],'real':['history']}

def slug(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

characters=[]
seen=set()
for work,medium,defaults,rows in GROUPS:
  for raw in rows.strip().splitlines():
    if not raw.strip(): continue
    parts=raw.strip().split('|')
    if len(parts)!=3: raise ValueError((work,raw))
    name,article,custom=map(str.strip,parts)
    cid=slug(work+'-'+name)
    if cid in seen: raise ValueError('Duplicate '+cid)
    seen.add(cid)
    is_real='real' in defaults.split()
    tags=set(defaults.split())|set(custom.split())
    for t in list(tags):
        if t in SYNONYMS: tags.add(SYNONYMS[t])
    tags={t for t in tags if t in LINKS}
    tags.add('real' if is_real else 'fictional')
    for i in range(3):
        for key in list(tags):
            tags.update(IMPLIES.get(key,[]))
    # deliberately keep metadata and cross-work traits, but never infer personal characteristics.
    characters.append(dict(id=cid,name=name,work=work,medium=medium,kind='real' if is_real else 'fictional',article=article if article!='-' else name,tags=sorted(tags)))

# Factual corrections to a small number of easy-to-misread entries.
byname={c['name']:c for c in characters}
for name,drop in {
  'Ariel':['sibling'], 'Mufasa':['elder'], 'Jessie':['singer'], 'The Doctor':['shapeshift'],
  'Robin Hood':['poor'], 'Spock':['telepathy'], 'Gonzo':['actor'], 'Dr. Zoidberg':['underwater'],
  'Shrek':['isolation'], 'Captain Ahab':['scar'], 'Scar':['scar'], 'Samus Aran':['orphan'],
}.items():
    if name in byname:
      byname[name]['tags']=sorted(set(byname[name]['tags'])-set(drop))

# Optional user-added characters. Keep custom rows in a separate file so regeneration is safe.
custom_path = HERE / 'data' / 'custom_characters.json'
if custom_path.exists():
  for entry in json.loads(custom_path.read_text(encoding='utf-8')):
    required={'name','work','medium','kind','article','tags'}
    if not required.issubset(entry): raise ValueError(f'Custom entry missing required fields: {entry}')
    if entry['kind'] not in ('real','fictional'): raise ValueError('kind must be real or fictional')
    custom_id=slug(entry['work']+'-'+entry['name'])
    if custom_id in seen: raise ValueError('Duplicate custom character: '+custom_id)
    seen.add(custom_id)
    tags=set(entry['tags'])
    invalid=tags-set(LINKS)
    if invalid: raise ValueError(f'Unknown trait(s) for {entry["name"]}: {sorted(invalid)}')
    tags.add(entry['kind'])
    for _ in range(3):
      for tag in list(tags): tags.update(IMPLIES.get(tag,[]))
    extra={key:entry[key] for key in ('imageUrl','imageSource') if entry.get(key)}
    characters.append(dict(id=custom_id,name=entry['name'],work=entry['work'],medium=entry['medium'],kind=entry['kind'],article=entry['article'],tags=sorted(tags),**extra))

# E.g. a recurring link must have enough candidates ACROSS distinct stories (not just one franchise).
from collections import Counter, defaultdict
counts=Counter(t for c in characters for t in c['tags'])
works=defaultdict(set)
for c in characters:
    for t in c['tags']: works[t].add(c['id'] if c['kind']=='real' else c['work'])
linkdefs=[]
for key,label in LINKS.items():
    if key in NEVER_LINK:continue
    count=counts.get(key,0)
    if count>=MIN_POOL and len(works[key])>=4 and count<=len(characters)*.6:
        linkdefs.append({'id':key,'label':label,'pool':count,'works':len(works[key])})
linkdefs.sort(key=lambda x:x['id'])

out={'version':1,'source':'Hand-curated seed catalogue; no generative AI or paid service used.','characters':characters,'links':linkdefs}
(HERE/'data'/'catalog.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print(f"{len(characters)} characters / {len(LINKS)} defined traits / {len(linkdefs)} qualified round links")
print('Traits per character:',min(map(lambda c:len(c['tags']),characters)),round(sum(len(c['tags']) for c in characters)/len(characters),1),max(map(lambda c:len(c['tags']),characters)))
print('Largest qualified links:', sorted(((x['id'],x['pool']) for x in linkdefs),key=lambda a:-a[1])[:20])
print('Smallest qualified links:', sorted(((x['id'],x['pool']) for x in linkdefs),key=lambda a:a[1])[:20])
