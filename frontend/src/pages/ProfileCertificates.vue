<template>
	<div class="mt-7 mb-10">
		<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
			{{ __('Certificates') }}
		</h2>
		<div
			v-if="certificates.data?.length"
			class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
		>
			<div
				v-for="certificate in certificates.data"
				:key="certificate.name"
				class="flex flex-col bg-surface-white border rounded-lg p-3 cursor-pointer hover:bg-surface-menu-bar"
				@click="openCertificate(certificate)"
			>
				<div class="font-medium leading-5 mb-2 text-ink-gray-9">
					{{ certificate.course_title || certificate.batch_title }}
				</div>
				<div
					v-if="certificate.serial_number"
					class="text-xs text-ink-gray-5 mt-1"
				>
					{{ __('Certificate No.') }}: {{ certificate.serial_number }}
				</div>
				<div class="flex items-center justify-between mt-2">
					<div class="flex items-center space-x-2">
						<Badge v-if="certificate.revoked" theme="red">
							{{ __('Revoked') }}
						</Badge>
						<a
							v-if="certificate.verification_token"
							:href="`/verify/${certificate.verification_token}`"
							target="_blank"
							class="text-xs text-ink-blue-3 hover:underline"
							@click.stop
						>
							{{ __('Verify') }}
						</a>
					</div>
					<Button
						v-if="canRevoke && !certificate.revoked"
						size="sm"
						variant="subtle"
						theme="red"
						@click.stop="openRevoke(certificate)"
					>
						{{ __('Revoke') }}
					</Button>
				</div>
			</div>
		</div>
		<div v-else class="text-sm italic text-ink-gray-5">
			{{ __('You have not received any certificates yet.') }}
		</div>
		<Dialog
			v-model="showRevoke"
			:options="{
				title: __('Revoke Certificate'),
				actions: [
					{
						label: __('Revoke'),
						variant: 'solid',
						theme: 'red',
						onClick: ({ close }) => revokeCertificate(close),
					},
				],
			}"
		>
			<template #body-content>
				<FormControl
					v-model="revokeReason"
					type="textarea"
					:label="__('Reason')"
					:required="true"
				/>
			</template>
		</Dialog>
	</div>
</template>
<script setup>
import {
	Badge,
	Button,
	call,
	createListResource,
	Dialog,
	FormControl,
	toast,
} from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'
import { cleanError } from '@/utils'

const user = inject('$user')
const canRevoke = computed(
	() => user.data?.is_moderator || user.data?.is_system_manager,
)
const showRevoke = ref(false)
const revokeReason = ref('')
const revokeTarget = ref(null)
const props = defineProps({
	profile: {
		type: Object,
		required: true,
	},
})

onMounted(() => {
	if (props.profile.data?.name) {
		certificates.reload()
	}
})

const certificates = createListResource({
	doctype: 'LMS Certificate',
	filters: {
		member: props.profile.data?.name,
	},
	fields: [
		'name',
		'course_title',
		'batch_title',
		'template',
		'serial_number',
		'verification_token',
		'revoked',
	],
	cache: ['certificates', props.profile.data?.name],
})

const openRevoke = (certificate) => {
	revokeTarget.value = certificate.name
	revokeReason.value = ''
	showRevoke.value = true
}

const revokeCertificate = (close) => {
	call('lms.lms.doctype.lms_certificate.lms_certificate.revoke_certificate', {
		name: revokeTarget.value,
		reason: revokeReason.value,
	})
		.then(() => {
			toast.success(__('Certificate revoked'))
			certificates.reload()
			close()
		})
		.catch((err) => {
			toast.error(cleanError(err.messages?.[0]) || err.message || err)
		})
}

const openCertificate = (certificate) => {
	window.open(
		`/api/method/frappe.utils.print_format.download_pdf?doctype=LMS+Certificate&name=${
			certificate.name
		}&format=${encodeURIComponent(certificate.template)}&no_letterhead=1`,
	)
}
</script>
