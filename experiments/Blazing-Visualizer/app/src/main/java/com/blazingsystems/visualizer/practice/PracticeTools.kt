package com.blazingsystems.visualizer.practice
import com.blazingsystems.visualizer.project.NoteEvent
import com.blazingsystems.visualizer.analysis.validateNote
import com.blazingsystems.visualizer.playback.PlaybackState
import java.io.*
import kotlin.math.roundToLong
object NoteNames {
 fun name(midiPitch:Int,preferFlats:Boolean=false,displayTranspose:Int=0):String{require(midiPitch in 0..127);val pitch=midiPitch+displayTranspose;val names=if(preferFlats)arrayOf("C","D♭","D","E♭","E","F","G♭","G","A♭","A","B♭","B") else arrayOf("C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B");return names[Math.floorMod(pitch,12)]+(Math.floorDiv(pitch,12)-1)}
}
object PracticeClock {fun sourceTimeUs(state:PlaybackState)=state.sourceTimeUs}
object NoteExport {
 fun writeMidi(events:List<NoteEvent>,output:OutputStream){data class Message(val tick:Long,val on:Boolean,val pitch:Int,val velocity:Int)
  val messages=events.flatMap{n->validateNote(n);listOf(Message((n.startUs*960.0/1_000_000).roundToLong(),true,n.pitch,(n.amplitude*127).toInt().coerceIn(1,127)),Message((n.endUs*960.0/1_000_000).roundToLong(),false,n.pitch,0))}.sortedWith(compareBy<Message>{it.tick}.thenBy{it.on}.thenBy{it.pitch})
  val track=ByteArrayOutputStream();track.write(byteArrayOf(0,0xff.toByte(),0x51,3,7,0xa1.toByte(),0x20))
  fun variable(value:Long){require(value in 0..0x0fffffff);var n=value;val b=mutableListOf((n and 127).toInt());n=n shr 7;while(n>0){b.add(0,((n and 127) or 128).toInt());n=n shr 7};b.forEach(track::write)}
  var previous=0L;messages.forEach{variable(it.tick-previous);track.write(if(it.on)0x90 else 0x80);track.write(it.pitch);track.write(it.velocity);previous=it.tick};track.write(byteArrayOf(0,0xff.toByte(),0x2f,0))
  DataOutputStream(output).apply{writeBytes("MThd");writeInt(6);writeShort(0);writeShort(1);writeShort(480);writeBytes("MTrk");writeInt(track.size());track.writeTo(this);flush()}
 }
 fun writeCsv(events:List<NoteEvent>,output:OutputStream){fun quote(value:String)="\""+value.replace("\"","\"\"")+"\"";val writer=output.bufferedWriter(Charsets.UTF_8);writer.write("id,pitch,note,start_us,end_us,amplitude,activation,provenance\r\n");events.sortedBy{it.startUs}.forEach{n->validateNote(n);writer.write("${quote(n.id)},${n.pitch},${quote(NoteNames.name(n.pitch))},${n.startUs},${n.endUs},${n.amplitude},${n.activation},${n.provenance}\r\n")};writer.flush()}
}
