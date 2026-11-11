$envFile = ".env"
$tokenNames = @("MCP_TOKEN", "LLAMA_API_KEY")

foreach ($name in $tokenNames) {
    if (Test-Path $envFile) {
        # If the variable exists and is not empty, skip to the next one
        if (Select-String -Path $envFile -Pattern "^$name=\S" -Quiet) { continue }
        
        # If the variable exists but is empty, throw an error and exit
        if (Select-String -Path $envFile -Pattern "^$name=" -Quiet) {
            Write-Error "$name is empty in .env. Fill it in or delete that line."
            exit 1
        }
    }

    # Generate a 24-byte random hex string (equivalent to openssl rand -hex 24)
    $b = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    $token = ($b | ForEach-Object { $_.ToString('x2') }) -join ''

    # Ensure the file ends with a newline before appending
    if ((Test-Path $envFile) -and ((Get-Content $envFile -Raw) -notmatch "\n$")) { 
        Add-Content $envFile "" 
    }

    # Append the new token to the .env file
    Add-Content -Path $envFile -Value "$name=$token" -Encoding ascii
    Write-Host "Added $name to .env."
}