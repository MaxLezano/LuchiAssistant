# Lectura y escritura de credenciales genéricas del Administrador de credenciales de Windows (CredRead/CredWrite).
# El secreto se guarda en UTF-16, igual que lo lee el crate `keyring` de Rust que va a usar la app.

$fuente = @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class LuchiCred {
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
  struct CREDENTIAL {
    public int Flags; public int Type; public string TargetName; public string Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public int CredentialBlobSize; public IntPtr CredentialBlob; public int Persist;
    public int AttributeCount; public IntPtr Attributes; public string TargetAlias; public string UserName;
  }
  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  static extern bool CredWrite(ref CREDENTIAL c, int flags);
  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  static extern bool CredRead(string target, int type, int flags, out IntPtr c);
  [DllImport("advapi32.dll")] static extern void CredFree(IntPtr c);

  const int GENERIC = 1, LOCAL_MACHINE = 2;

  public static void Write(string target, string user, string secret) {
    byte[] blob = Encoding.Unicode.GetBytes(secret);
    var c = new CREDENTIAL { Type = GENERIC, TargetName = target, UserName = user, Persist = LOCAL_MACHINE,
                             CredentialBlobSize = blob.Length, CredentialBlob = Marshal.AllocHGlobal(blob.Length) };
    try {
      Marshal.Copy(blob, 0, c.CredentialBlob, blob.Length);
      if (!CredWrite(ref c, 0)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    } finally { Marshal.FreeHGlobal(c.CredentialBlob); }
  }

  public static string Read(string target) {
    IntPtr p;
    if (!CredRead(target, GENERIC, 0, out p)) return null;
    try {
      var c = (CREDENTIAL)Marshal.PtrToStructure(p, typeof(CREDENTIAL));
      return Marshal.PtrToStringUni(c.CredentialBlob, c.CredentialBlobSize / 2);
    } finally { CredFree(p); }
  }
}
"@
if (-not ("LuchiCred" -as [type])) { Add-Type -TypeDefinition $fuente }

function Set-LuchiCredencial([string]$Destino, [string]$Usuario, [string]$Secreto) { [LuchiCred]::Write($Destino, $Usuario, $Secreto) }
function Get-LuchiCredencial([string]$Destino) { [LuchiCred]::Read($Destino) }

Export-ModuleMember -Function Set-LuchiCredencial, Get-LuchiCredencial
