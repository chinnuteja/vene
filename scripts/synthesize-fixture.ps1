# Original test speech. Input and PCM stay in memory; no audio/transcript files.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Speech
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$synthesizer=[System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    $format=[System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(24000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
    while (($speechLine=[Console]::In.ReadLine()) -ne $null) {
        $pcmMemory=$null;$speechInput=$null;$encoded=$null
        try {
            $speechInput=$speechLine | ConvertFrom-Json
            if (-not $speechInput.text -or $speechInput.text.Length -gt 600) { throw 'Invalid speech input.' }
            $pcmMemory=[IO.MemoryStream]::new()
            $synthesizer.SetOutputToAudioStream($pcmMemory,$format)
            if ($speechInput.voice) { $synthesizer.SelectVoice([string]$speechInput.voice) }
            $synthesizer.Speak([string]$speechInput.text)
            $encoded=[Convert]::ToBase64String($pcmMemory.ToArray())
            [Console]::Out.WriteLine((@{sample_rate=24000;voice=$synthesizer.Voice.Name;pcm=$encoded} | ConvertTo-Json -Compress))
        } catch { [Console]::Out.WriteLine('{"error":"offline_synthesis_failed"}') }
        finally {
            $synthesizer.SetOutputToNull()
            if($pcmMemory){$pcmMemory.Dispose()}
            $speechInput=$null;$encoded=$null;$speechLine=$null;$pcmMemory=$null
        }
    }
} finally { $synthesizer.Dispose() }
