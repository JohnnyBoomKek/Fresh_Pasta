 pasta
    pk  |   vk_id   |   likes   |   text    |   audio      
user
    pk  |   name    |   read(list of pasta_pk's(find it a bit hard to implement for now))   |   last_read    

Done so far:
    db.py
    init db 
    update likes in the db 
    add new posts to the db

    bot.py
    /start command


Expected pattern: 

1. User is promted to register. Upon doing so, user info gets added to the db
2. Current id of the last added (post -1) is assigned to the user as the last_read value. 
3. User is informed on how many new posts are yet to be seen. If the number of unread posts 
is greater than zero user is provided with the /fresh_pasta command (probably in a shape of the a button).
4. User recieves the post and an option to convert the post to tts with the /audio command. 
5. Steps 2 to 5 repeat until the user has no more unread posts.
6. /stop command stops the bot from notifying the user and removes the user from the DB


So the steps above can pretty much be the states for the ConversationHandler
with 1. being the entry point
2-5 Conversation cycle(?)
6 would be the fallback the fallback



Future features:
* Polls and likes
* Add new sources 
* Audio
* Ability to post your own pasta that will undergo moderation 
* Read random post
* Daily Jobs
* Pics with posts



Bugs:
* fix the issue with adding post to the DB with no text
