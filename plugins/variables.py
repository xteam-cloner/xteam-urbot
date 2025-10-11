# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
✘ Commands Available -

• `{i}get var <variable name>`
   Get value of the given variable name.

• `{i}get type <variable name>`
   Get variable type.

• `{i}get db <key>`
   Get db value of the given key.

• `{i}get keys`
   Get all redis keys.
"""

import os
import io
from . import eor, get_string, udB, ultroid_cmd


@ultroid_cmd(pattern="get($| (.*))", fullsudo=True)
async def get_var(event):
    try:
        # Menghindari error jika tidak ada argumen sama sekali
        # Menggunakan maxsplit=1 agar argumen yang tersisa menjadi satu string
        opt = event.text.split(maxsplit=1)[1].split()[0]
    except IndexError:
        return await event.eor(f"what to get?\nRead `{HNDLR}help variables`")
    
    # Pesan awal 'Processing...'
    x = await event.eor(get_string("com_1"))
    
    # Logic untuk perintah yang membutuhkan 'varname'
    if opt not in ["keys"]:
        try:
            # Mengambil varname sebagai argumen kedua
            varname = event.text.split(maxsplit=2)[2]
        except IndexError:
            # Karena opt sudah diambil, error ini berarti varname hilang
            return await eor(x, "Var name is missing!", time=5) # Pesan diperjelas

    if opt == "var":
        
        # 1. Cek di Redis (udB.get_key)
        val = udB.get_key(varname)
        var_type = "Redis Key."
        
        # 2. Cek di Environment Variables jika tidak ditemukan di Redis
        if val is None:
            val = os.getenv(varname)
            var_type = "Env Var."

        if val is not None:
            # 3. Ubah nilai menjadi string dan terapkan penanganan pesan panjang
            val_str = str(val)
            
            # --- START FIX: Penanganan MessageTooLongError ---
            if len(val_str) > 4000:
                # Jika terlalu panjang, kirim sebagai file .txt
                with io.StringIO(f"Variable: {varname}\nType: {var_type}\n\nValue:\n{val_str}") as f:
                    f.name = f"{varname}_value.txt"
                    
                    # Kirim file ke chat
                    await event.client.send_file(
                        event.chat_id, 
                        f, 
                        caption=f"**Variable** - `{varname}`\n**Type**: {var_type}\nNilai terlalu panjang, dikirim sebagai file."
                    )
                # Edit pesan awal menjadi pemberitahuan
                await x.edit(f"**Variable** - `{varname}`\n**Type**: {var_type}\nNilai telah dikirim sebagai file `.txt`.")
            else:
                # Jika pendek, edit seperti biasa
                await x.edit(
                    f"**Variable** - `{varname}`\n**Value**: `{val_str}`\n**Type**: {var_type}"
                )
            # --- END FIX ---

        else:
            await eor(x, "Such a var doesn't exist!", time=5)

    elif opt == "type":
        # ... (Logika untuk 'type' tetap sama)
        c = 0
        # try redis
        val = udB.get_key(varname)
        if val is not None:
            c += 1
            await x.edit(f"**Variable** - `{varname}`\n**Type**: Redis Key.")
        # try env vars
        val = os.getenv(varname)
        if val is not None:
            c += 1
            await x.edit(f"**Variable** - `{varname}`\n**Type**: Env Var.")

        if c == 0:
            await eor(x, "Such a var doesn't exist!", time=5)

    elif opt == "db":
        val = udB.get(varname)
        if val is not None:
            # --- Logika penanganan pesan panjang untuk 'db' (Sudah Benar) ---
            val_str = str(val)
            if len(val_str) > 4000:
                with io.StringIO(f"Key: {varname}\n\nValue:\n{val_str}") as f:
                    f.name = f"{varname}_value.txt"
                    
                    # Kirim file ke chat
                    await event.client.send_file(
                        event.chat_id, 
                        f, 
                        caption=f"**Key** - `{varname}`\nNilai terlalu panjang, dikirim sebagai file."
                    )
                # Edit pesan awal menjadi pemberitahuan
                await x.edit(f"**Key** - `{varname}`\nNilai telah dikirim sebagai file `.txt`.")
            else:
                # Jika pendek, edit seperti biasa
                await x.edit(f"**Key** - `{varname}`\n**Value**: `{val_str}`")
        else:
            await eor(x, "No such key!", time=5)

    elif opt == "keys":
        keys = sorted(udB.keys())
        msg = "".join(
            f"• `{i}`" + "\n"
            for i in keys
            if not i.isdigit()
            and not i.startswith("-")
            and not i.startswith("_")
            and not i.startswith("GBAN_REASON_")
        )
        
        # --- Logika penanganan pesan panjang untuk 'keys' (Sudah Benar) ---
        if len(msg) > 4000:
            # Buat file di memori (StringIO)
            with io.StringIO(f"List of DB Keys :\n\n{msg}") as f:
                f.name = "db_keys_list.txt"
                
                # Kirim file ke chat tempat perintah dipicu
                await event.client.send_file(
                    event.chat_id, 
                    f, 
                    caption=f"**List of DB Keys** (Terlalu panjang, dikirim sebagai file)"
                )
                
            # Edit pesan awal dengan pesan sukses/pemberitahuan
            await x.edit("✅ Daftar kunci database telah dikirim sebagai file `.txt`.")
            
        else:
            # Jika pendek, edit pesan seperti biasa
            await x.edit(f"**List of DB Keys :**\n{msg}")
