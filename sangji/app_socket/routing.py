from django.urls import path
from . import consumers
from app_socket.consumer import musclefunction, faceIdentification, coaching

websocket_urlpatterns = [
    # 앱으로부터 frame 수신 -> coordinates 도출 값 반환 (socket 통신) -> OSI 7 Application Layer 통신
    # 연결 끊임이 잦다면, TCP, UDP와 같은 네트워크 Layer 통신도 고려해야 함.
    path('ws/inference/frame', consumers.PoseEstimationConsumer.as_asgi()), 
    path("ws/bpm", consumers.HeartRateConsumer.as_asgi()),
    path('ws/game/mole',consumers.MoleGameConsumer.as_asgi()),
    path('ws/game/mole/data', consumers.MoleGameDataConsumer.as_asgi()),
    path('ws/revitalizationIsometricLatPulldownConsumer', consumers.RevitalizationIsometricLatPulldownConsumer.as_asgi()),
    # path('ws/test', consumers.TestConsumer.as_asgi()),
    path('ws/rom/elbow',consumers.ROMElbowConsumer.as_asgi()),
    path('ws/rom/shoulder1',consumers.ROMShoulder1Consumer.as_asgi()),
    path('ws/rom/shoulder2',consumers.ROMShoulder2Consumer.as_asgi()),
    # 해부학적 자세 ROM
    # path('ws/rom/anatomical')
    # 머리 외측굴곡
    path('ws/rom/head/lateralflextion', musclefunction.ROMHeadLateralflextion.as_asgi()),
    # 머리 굴곡
    path('ws/rom/head/flextion', musclefunction.ROMHeadflextion.as_asgi()),
    # 머리 과신전
    path('ws/rom/head/extension', musclefunction.ROMHeadflextion.as_asgi()),
    path('ws/revitalizationIsometricChestpressConsumer', consumers.RevitalizationIsometricChestpressConsumer.as_asgi()),
    path('ws/IsometricExerciseTestLatPullDownConsumer', consumers.IsometricExerciseTestLatPullDownConsumer.as_asgi()),
    path('ws/IsokineticsExerciseTestLatPullDownConsumer', consumers.IsokineticsExerciseTestLatPullDownConsumer.as_asgi()),
    path('ws/IsotonicExerciseTestLatPullDownConsumer', consumers.IsotonicExerciseTestLatPullDownConsumer.as_asgi()),
    path('musclefunction/range', musclefunction.MuscleFunctionRangeConsumer.as_asgi()),
    path("ws/normalpose", consumers.NormalPoseEstimation.as_asgi()),
    # Face Identification
    path("ws/face/identification", faceIdentification.FaceIdentificationConsumer.as_asgi()),
    # AI Coaching Consumer
    path("ws/ai/coach/poseestimation", coaching.CoachingPoseEstimation.as_asgi()),
]

