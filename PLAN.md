Goal: The bot should be able to join the user's voice channel, listen to the audio, transcribe it to text using an external Speech-to-Text (STT) service/library, and potentially act upon that text (e.g., print it, 
feed it to Gemini).                                                                                                                                                                                                   

Core Components & Challenges:                                                                                                                                                                                         

 1 Voice Channel Connection: Joining and leaving the user's voice channel on command.                                                                                                                                 
 2 Audio Reception: Capturing raw audio data from potentially multiple users in the channel. discord.py provides mechanisms for this using VoiceClient.listen() and Sink objects.                                     
 3 Audio Processing: The received audio data (likely PCM) needs to be processed and potentially converted to a format suitable for the STT engine.                                                                    
 4 Speech-to-Text (STT): Integrating an external library or cloud service to convert the audio data into text. This is the most complex part and requires choosing a specific STT solution.                           
 5 Handling Transcriptions: Deciding what to do with the transcribed text (log, display, send to AI).                                                                                                                 
 6 Concurrency & Resource Management: Handling audio from multiple users simultaneously and managing the resources (CPU, network, API quotas) required for STT.                                                       

Plan:                                                                                                                                                                                                                 

Phase 1: Basic Voice Connection & Audio Sink Setup                                                                                                                                                                    

 1 Add Voice Intents: Ensure the necessary voice_states intent is enabled (it's part of Intents.default(), but good to be aware of).                                                                                  
 2 Install Dependencies: We'll need libraries for STT. A popular choice is OpenAI's Whisper. Let's tentatively plan for that:                                                                                         
    • pip install -U openai-whisper (or potentially a specific fork/version)                                                                                                                                          
    • Ensure ffmpeg is installed and accessible in the system PATH (Whisper often relies on it).                                                                                                                      
 3 !listen Command:                                                                                                                                                                                                   
    • Create a new bot command (e.g., !listen).                                                                                                                                                                       
    • Check if the invoking user (ctx.author) is in a voice channel. If not, reply with an error.                                                                                                                     
    • If the bot is already connected to a voice client in that guild, potentially disconnect first or handle appropriately (e.g., move channels or refuse).                                                          
    • Connect the bot to the user's voice channel (ctx.author.voice.channel.connect()). Store the resulting VoiceClient object.                                                                                       
    • Reply to the user confirming the bot has joined and is listening.                                                                                                                                               
 4 !stoplisten Command:                                                                                                                                                                                               
    • Create a new bot command (e.g., !stoplisten).                                                                                                                                                                   
    • Check if the bot has an active VoiceClient in the guild (ctx.voice_client). If not, reply that it's not listening.                                                                                              
    • If connected, call vc.disconnect() on the voice client.                                                                                                                                                         
    • Clean up any ongoing listening processes (important for later phases).                                                                                                                                          
    • Reply confirming the bot has stopped listening and left the channel.                                                                                                                                            
 5 Audio Sink:                                                                                                                                                                                                        
    • When the bot connects via !listen, start listening using vc.listen(sink).                                                                                                                                       
    • We need a custom Sink class (inheriting from discord.Sink). This sink's primary role initially will be to receive audio data packets.                                                                           
    • The Sink needs a write(data, user) method, which discord.py calls with raw audio data and the speaking user.                                                                                                    
    • For now, the sink might just log that it received data or write it to temporary files per user.                                                                                                                 

Phase 2: STT Integration (using Whisper as example)                                                                                                                                                                   

 1 Whisper Setup:                                                                                                                                                                                                     
    • Load the Whisper model (e.g., whisper.load_model("base") or another size) when the bot starts or when listening begins. Be mindful of model download time and resource usage.                                   
 2 Modify Sink:                                                                                                                                                                                                       
    • The Sink needs to accumulate audio data for each user.                                                                                                                                                          
    • Decide on a strategy for when to transcribe:                                                                                                                                                                    
       • Fixed Duration: Transcribe every X seconds of audio per user.                                                                                                                                                
       • Silence Detection: Accumulate audio until a period of silence is detected for a user, then transcribe that segment. (More complex but often preferred).                                                      
    • When a transcription trigger occurs:                                                                                                                                                                            
       • Take the accumulated raw audio data (likely PCM).                                                                                                                                                            
       • Convert it to the format Whisper expects (requires knowing sample rate, channels, etc., provided by Discord, and potentially using libraries like numpy and soundfile or pydub).                             
       • Run the Whisper transcription (model.transcribe(...)) on the audio data. This is computationally intensive and should likely be run in an executor (loop.run_in_executor) to avoid blocking the bot.         
       • Clear the accumulated audio buffer for that user.                                                                                                                                                            
 3 Handle Transcription Results:                                                                                                                                                                                      
    • The Sink (or a callback mechanism) receives the transcribed text from Whisper.                                                                                                                                  
    • Associate the text with the user ID provided to the write method.                                                                                                                                               

Phase 3: Action on Transcription                                                                                                                                                                                      

 1 Output: Decide what to do with the (user, text) pair:                                                                                                                                                              
    • Log: Print f"{user.name}: {text}" to the console.                                                                                                                                                               
    • Text Channel: Send the transcription to the text channel where !listen was invoked (or a designated logging channel).                                                                                           
    • AI Interaction: Feed the text into the get_gemini_response function (similar to on_message), potentially prefixing it with the user's name for context. Send Gemini's response back to the text channel.        
 2 Implement: Add the chosen action logic where the transcription result is received.                                                                                                                                 

Phase 4: Refinements                                                                                                                                                                                                  

 1 Error Handling: Add robust error handling for voice connection failures, STT errors, invalid audio formats, etc.                                                                                                   
 2 Resource Management: Ensure temporary audio files are cleaned up. Monitor CPU/memory usage, especially with larger Whisper models. Consider limitations on concurrent transcriptions if needed.                    
 3 User Feedback: Provide clearer messages (e.g., "Transcription error for user X", "User Y said: ...").                                                                                                              
 4 Configuration: Make channel names, STT models, etc., configurable if desired.                                                                                                                                      
