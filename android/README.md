# Bondi Android — 0.1.0-alpha.1

App nativa Kotlin / Jetpack Compose: catálogo de las 19 líneas solicitadas,
búsqueda, detalle y favoritos persistidos localmente. Funciona offline porque el
catálogo está embebido. No contiene todavía recorridos, horarios, mapas, routing,
Room, Hilt ni conexión al backend. La UI lo indica expresamente.

Requiere JDK 17 o 21, Android SDK 35 y build-tools 35.0.0.

```sh
./gradlew testDebugUnitTest assembleDebug
```

El release usa `assembleRelease` y una firma propia de previsualización mediante
`BONDI_KEYSTORE`, `BONDI_STORE_PASSWORD`, `BONDI_KEY_PASSWORD`, alias `bondi-preview`.
No subir el keystore ni sus contraseñas. Conservarlos para actualizar el APK sin
reinstalar. Application ID independiente: `ar.com.bondi.preview`.

La firma local de esta entrega se conserva en `.signing/` (ignorada por Git y Docker).
Guardar una copia segura del keystore y sus credenciales: perderlos impide actualizar
instalaciones existentes con la misma firma. No distribuir estos archivos junto al APK.

Con esas variables configuradas, generar y validar el release:

```sh
./gradlew --no-daemon testDebugUnitTest lintRelease assembleRelease
```

Resultado: `app/build/outputs/apk/release/app-release.apk`. Las pruebas del catálogo
usan datos del alcance solicitado; no verifican que las líneas estén operativas.
