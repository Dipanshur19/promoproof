// Original synthetic fixture. No Kuku screenplay text is bundled with this app.
export function demoFiles() {
  const episodes = [
    [
      ["MARA (Furious)", 0, 3, '"You stole my company. Give me back the patent."'],
      ["VICTOR (Cold)", 4, 8, '"You signed the transfer, Mara. Every camera in this room saw it."'],
      ["ACTION", 8, 11, "Mara slaps the forged contract onto the gala table."],
      ["SOUND FX", 8.2, 9, "A sharp slap as paper hits the table."],
      ["MARA (Defiant)", 12, 16, '"That signature is not mine. Let the board hear the recording."'],
      ["VICTOR (Threatening)", 18, 22, '"Play that file and your brother loses his scholarship."'],
      ["MARA (Shaken)", 24, 27, '"You promised you would leave him out of this."'],
      ["ELIAS (Calm)", 30, 34, '"She has a witness. I was in the archive that night."'],
      ["VICTOR (Alarmed)", 36, 39, '"Who are you, and how did you get past security?"'],
      ["ELIAS (Firm)", 42, 46, '"Ask your chairman why he gave me the original key."'],
      ["MARA (Suspicious)", 49, 53, '"You said the chairman was dead. What else did you hide?"'],
      ["VICTOR (Urgent)", 56, 59, '"Security, lock the doors. Nobody leaves with that evidence."'],
      ["ACTION", 60, 64, "Victor reaches for the recorder. Mara steps behind Elias."],
      ["MARA (Urgent)", 65, 69, '"The backup is already scheduled. Who do you think receives it first?"'],
    ],
    [
      ["MARA (Accusing)", 0, 3, '"You lied to the board. My father never sold this patent."'],
      ["VICTOR (Dismissive)", 5, 9, '"Your father left debts. I made them disappear."'],
      ["ELIAS (Measured)", 12, 16, '"He also left a sealed envelope with one condition."'],
      ["MARA (Wary)", 18, 22, '"Nobody opens it until the original inventor returns."'],
      ["VICTOR (Cruel)", 25, 29, '"An inventor who has been missing for ten years cannot save you."'],
      ["MARA (Defiant)", 32, 36, '"Then explain why his security badge was used this morning."'],
      ["ACTION", 38, 41, "Victor punches the access console; the room lights turn red."],
      ["SOUND FX", 38.4, 39.5, "A hard punch followed by an electronic alarm."],
      ["ELIAS (Urgent)", 43, 47, '"The badge holder is inside this building. We have three minutes."'],
      ["MARA (Determined)", 50, 54, '"Open the east stairwell. I know who is waiting there."'],
      ["VICTOR (Threatening)", 58, 62, '"Take one more step and I release your brother’s confession."'],
      ["MARA (Shocked)", 65, 69, '"What confession? What did you make him sign?"'],
    ],
    [
      ["ELIAS (Commanding)", 0, 3, '"Arrest me instead. Mara never touched the safe."'],
      ["SECURITY CHIEF (Skeptical)", 5, 9, '"The camera shows her entering the archive at midnight."'],
      ["MARA (Urgent)", 12, 16, '"The clock in that video was changed. Check the reflection."'],
      ["VICTOR (Angry)", 19, 23, '"You are all wasting time. Take her away now."'],
      ["ACTION", 25, 28, "The security chief turns the monitor toward the assembled board."],
      ["SECURITY CHIEF (Stunned)", 30, 34, '"That is not Mara’s reflection. It is someone standing behind you."'],
      ["MARA (Quiet)", 37, 41, '"Victor, tell them why you are wearing my father’s watch."'],
      ["VICTOR (Unsteady)", 44, 48, '"He gave it to me before he left. We were partners."'],
      ["ELIAS (Firm)", 51, 55, '"Then you will recognize his voice on this recording."'],
      ["MARA (Urgent)", 58, 62, '"Wait. Before you play it, who sent you the envelope?"'],
      ["ELIAS (Grave)", 65, 69, '"Your father. And he says one person in this room cannot be trusted."'],
    ],
  ] as (string | number)[][][];
  const tc = (n: number) => `${String(Math.floor(n / 60)).padStart(2,"0")}:${(n%60).toFixed(3).padStart(6,"0")}`;
  return episodes.map((lines,i) => {
    const text = `EPISODE NUMBER: Episode ${i+1}\nEPISODE LOGLINE: Original synthetic corporate revenge drama for software testing.\nCONTINUITY NOTES: Mara challenges a forged patent transfer at a gala. No external story material.\n\n--- SCRIPT START ---\n\nSCENE 01\nScene heading: INT. GALA ARCHIVE - NIGHT\nScene start: 00:00.000\nScene end: 01:12.000\n\n**CAMERA:** Start: (00:00.000) | End: (01:12.000)\nAlternating reaction shots and legible views of the contract and recorder.\n\n` +
      lines.map(([label,start,end,text]) => `**${label}:** Start: (${tc(Number(start))}) | End: (${tc(Number(end))})\n${text}`).join("\n\n") + "\n\n--- SCRIPT END ---";
    return {name:`synthetic-episode-${i+1}.txt`,data:btoa(unescape(encodeURIComponent(text)))};
  });
}
