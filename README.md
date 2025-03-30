1. Text-to-Speech (TTS) Generation and Playback                                                                                                 

 • Goal: Convert text responses (primarily from Gemini via the !ask command) into audible speech and play it in the user's voice channel.       
 • Key Components:                                                                                                                              
    • gTTS library: Used to generate the audio file from text.                                                                                  
    • generate_tts_audio(text, filename) function (Lines 60-69):                                                                                
       • Takes a string (text) as input.                                                                                                        
       • Uses gTTS(text=text, lang='en') to create a TTS object.                                                                                
       • Saves the generated speech as an MP3 file (default: tts_response.mp3).                                                                 
       • Returns the filename if successful, None otherwise.                                                                                    
    • play_audio_in_vc(voice_channel, audio_path, playback_rate) function (Lines 71-119):                                                       
       • Takes the target discord.VoiceChannel, the path to the audio file (audio_path), and an optional playback_rate (defaulting to 1.0).     
       • Manages the bot's voice connection:                                                                                                    
          • Checks if the bot is already connected; if so, moves to the target channel if necessary (vc.move_to).                               
          • If not connected, it connects (vc.connect).                                                                                         
       • Handles playback rate: If playback_rate is not 1.0, it constructs ffmpeg_options using the atempo audio filter (e.g., '-filter:a       
         "atempo=1.5"') to speed up or slow down playback. It clamps the rate between 0.5x and 3.0x.                                            
       • Plays the audio using discord.FFmpegPCMAudio(audio_path, options=ffmpeg_options). This requires ffmpeg to be installed and accessible  
         in the system's PATH. discord.py uses ffmpeg to process and stream the audio.                                                          
       • Waits for playback to finish (while vc.is_playing(): await asyncio.sleep(1)).                                                          
       • Disconnects the voice client (vc.disconnect()) and cleans up the temporary audio file (os.remove).                                     
    • !ask Command Integration (Lines 296-304):                                                                                                 
       • After getting a text response from Gemini, it checks if the command user (ctx.author) is in a voice channel.                           
       • If yes, it calls generate_tts_audio (in an executor thread because gTTS.save can be blocking).                                         
       • If audio generation is successful, it calls play_audio_in_vc to play the generated file in the user's channel.                         

2. Voice Listening and Speech-to-Text (STT)                                                                                                     

 • Goal: Join a voice channel, listen to users speaking, convert their speech into text, and handle the transcription.                          
 • Key Components:                                                                                                                              
    • openai-whisper library: Used for the actual STT conversion. The model (tiny) is loaded at startup (Lines 31-39).                          
    • discord.py Voice Client & Sinks: The core mechanism for receiving audio.                                                                  
    • WhisperSink class (Lines 129-211): Inherits from discord.Sink. This is the heart of the listening process.                                
       • __init__: Stores a callback function (handle_transcription) to call when transcription is done. Initializes buffers for each user.     
       • write(data, user): This method is called automatically by discord.py whenever a user speaks and sends audio data (data is raw PCM). It 
         appends the data to a user-specific buffer (self.user_audio_buffers).                                                                  
       • Buffering & Triggering: It checks if the buffer size exceeds a limit defined by BUFFER_DURATION_SECONDS (currently 2 seconds). If it   
         does, it copies the buffered audio, clears the buffer, and schedules process_transcription to run asynchronously.                      
       • process_transcription(pcm_data, user):                                                                                                 
          • Audio Conversion: This is crucial. Discord sends audio as 48kHz, 16-bit, stereo PCM. Whisper expects 16kHz, 32-bit float, mono      
            audio. This function uses:                                                                                                          
             • audioop.ratecv: To resample from 48kHz to 16kHz.                                                                                 
             • audioop.tomono: To convert stereo to mono.                                                                                       
             • numpy: To convert the raw byte data (mono_data) into a NumPy array (audio_np), change the data type to float32, and normalize the
               values (audio_fp32).                                                                                                             
          • Transcription: Runs whisper_model.transcribe(audio_fp32, ...) in an executor thread (loop.run_in_executor) because transcription is 
            CPU-intensive and would block the bot's main loop.                                                                                  
          • Callback: Calls the stored handle_transcription function with the user and the resulting transcribed_text.                          
       • cleanup(): Called when the sink stops (e.g., via vc.disconnect). Closes any open buffers.                                              
    • handle_transcription(user, text) function (Lines 122-127): The simple callback function currently used. It just prints the user's name and
      the transcribed text to the console.                                                                                                      
    • !listen Command (Lines 320-359):                                                                                                          
       • Checks if the user is in a voice channel.                                                                                              
       • Connects or moves the bot to the user's voice channel.                                                                                 
       • Crucially, starts the listening process by attaching the sink: vc.listen(WhisperSink(handle_transcription)).                           
    • !stoplisten Command (Lines 362-373):                                                                                                      
       • Finds the voice client (vc).                                                                                                           
       • Disconnects the voice client (vc.disconnect()). This implicitly stops the listening process and triggers the WhisperSink.cleanup()     
         method.                                                                                                                                

In Summary:                                                                                                                                     

 • The bot can speak text responses in voice channels using gTTS to generate audio and discord.py's voice client (with ffmpeg) to play it,      
   supporting variable playback speed.                                                                                                          
 • The bot can listen in voice channels using discord.py's Sink mechanism. The custom WhisperSink buffers incoming audio, converts it to the    
   format required by Whisper using audioop and numpy, transcribes it using the openai-whisper library in a background thread, and then calls a 
   handler function with the resulting text. 

